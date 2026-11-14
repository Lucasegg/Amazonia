"""API do jogo; o cliente nunca decide resultados mecânicos nem movimento."""
import os
import logging
from random import SystemRandom

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.domain.inventory import ITEMS, InventoryRuleError, consume_item
from app.domain.rules import ORIGINS, Origin, RuleValidationError, resolve_check
from app.domain.world import (
    MAX_CELL_COORDINATE,
    MOVE_COST_MINUTES,
    apply_movement_needs,
    apply_rest_needs,
    build_map_data,
    cell_key,
    hex_distance,
)
from app.models import Campaign, Character, PointOfInterest, User
from app.schemas import AccountTokenRequest, AuthResponse, EmailAddressRequest, CampaignCreate, CampaignRead, CharacterCreate, CharacterRead, LoginRequest, MoveRequest, PasswordResetRequest, RegisterRequest, UseItemRequest, UserRead
from app.auth import clear_auth_attempts, clear_session_cookies, consume_account_token, create_account_token, get_current_user, hash_password, is_rate_limited, record_auth_attempt, set_csrf_cookie, set_session_cookies, verify_password
from app.email_delivery import send_account_email
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Amazonia API",
    version="0.5.0",
    description="API inicial do RPG Amazonia. Regras e movimentação são validadas no servidor.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "AMAZONIA_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def enforce_browser_origin(request: Request, call_next):
    """Bloqueia origens externas em operações mutáveis, inclusive login/cadastro."""
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin:
            allowed = {
                item.strip()
                for item in os.getenv(
                    "AMAZONIA_CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
                if item.strip()
            }
            if origin not in allowed:
                return JSONResponse(status_code=403, content={"detail": "Origem não autorizada."})
    return await call_next(request)


class CheckRequest(BaseModel):
    """Parâmetros de um teste; o D20 é produzido no servidor."""
    attribute_value: int = Field(ge=1, le=5)
    skill_level: int = Field(ge=0, le=5)
    difficulty: int
    situational_modifier: int = Field(default=0, ge=-2, le=2)


@app.get("/health", tags=["operacao"])
def health() -> dict[str, str]:
    """Verifica disponibilidade sem expor configuração."""
    return {"status": "ok", "service": "amazonia-api"}


@app.get("/api/v1/game/origins", tags=["jogo"])
def list_origins() -> list[dict[str, object]]:
    """Lista as três origens do primeiro protótipo."""
    return [
        {
            "id": profile.id.value,
            "label": profile.label,
            "starting_skills": dict(profile.starting_skills),
            "starting_items": list(profile.starting_items),
            "contextual_strength": profile.contextual_strength,
        }
        for profile in ORIGINS.values()
    ]


@app.post("/api/v1/game/checks", tags=["jogo"])
def perform_check(payload: CheckRequest) -> dict[str, object]:
    """Gera a rolagem aleatória no servidor e executa o cálculo do domínio."""
    try:
        result = resolve_check(
            roll=SystemRandom().randint(1, 20),
            attribute_value=payload.attribute_value,
            skill_level=payload.skill_level,
            difficulty=payload.difficulty,
            situational_modifier=payload.situational_modifier,
        )
    except RuleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "roll": result.roll,
        "attribute_modifier": result.attribute_modifier,
        "skill_level": result.skill_level,
        "situational_modifier": result.situational_modifier,
        "total": result.total,
        "difficulty": result.difficulty,
        "success": result.success,
        "margin": result.margin,
        "outcome": result.outcome,
    }


@app.get("/api/v1/game/origins/{origin_id}", tags=["jogo"])
def get_origin(origin_id: str) -> dict[str, object]:
    """Retorna o pacote de uma origem ou 404."""
    try:
        profile = ORIGINS[Origin(origin_id)]
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail="Origem não encontrada.") from exc
    return {
        "id": profile.id.value,
        "label": profile.label,
        "starting_skills": dict(profile.starting_skills),
        "starting_items": list(profile.starting_items),
        "contextual_strength": profile.contextual_strength,
    }


@app.get("/api/v1/auth/csrf", tags=["autenticacao"])
def csrf_token(request: Request, response: Response) -> dict[str, str]:
    """Entrega token CSRF ao frontend mesmo quando API e Web usam hosts distintos."""
    token = request.cookies.get("amazonia_csrf")
    return {"csrf_token": set_csrf_cookie(response, token)}


def _account_action_url(action: str, token: str) -> str:
    base = os.getenv("AMAZONIA_WEB_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/?{action}={token}"


def _verification_required() -> bool:
    return os.getenv("AMAZONIA_REQUIRE_EMAIL_VERIFICATION", "true").strip().lower() in {"1", "true", "yes"}


@app.post("/api/v1/auth/register", status_code=202, tags=["autenticacao"])
def register(payload: RegisterRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    """Cria conta e, por padrão, exige confirmação do endereço antes do login."""
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(db, "register_ip", client_ip, 5, timedelta(hours=1)):
        raise HTTPException(status_code=429, detail="Muitas tentativas de cadastro. Tente novamente mais tarde.")
    record_auth_attempt(db, "register_ip", client_ip)
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=409, detail="Este e-mail já possui uma conta.")
    user = User(email=payload.email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este e-mail já possui uma conta.") from exc
    db.refresh(user)
    if _verification_required():
        token = create_account_token(db, user, "verify_email", timedelta(hours=24))
        link = _account_action_url("verify", token)
        send_account_email(user.email, "Confirme sua conta Amazonia", f"Olá, {user.display_name}.\n\nConfirme seu e-mail em até 24 horas acessando:\n{link}\n\nSe você não criou esta conta, ignore esta mensagem.")
        return {"message": "Conta criada. Enviamos um link de confirmação para seu e-mail."}
    csrf_token = set_session_cookies(response, user.id, user.session_version)
    return {"user": user, "csrf_token": csrf_token}


@app.post("/api/v1/auth/verify-email", response_model=AuthResponse, tags=["autenticacao"])
def verify_email(payload: AccountTokenRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    """Confirma o e-mail com token de uso único e provisiona o owner por configuração."""
    user = consume_account_token(db, payload.token, "verify_email")
    if user is None:
        db.rollback()
        raise HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite outro e-mail de confirmação.")
    user.email_verified_at = datetime.now(timezone.utc)
    owner_email = os.getenv("AMAZONIA_OWNER_EMAIL", "").strip().lower()
    if owner_email and user.email.lower() == owner_email:
        user.role = "owner"
    db.commit()
    db.refresh(user)
    csrf_token = set_session_cookies(response, user.id, user.session_version)
    return {"user": user, "csrf_token": csrf_token}


@app.post("/api/v1/auth/resend-verification", status_code=202, tags=["autenticacao"])
def resend_verification(payload: EmailAddressRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    """Reenvia confirmação sem revelar se o endereço está cadastrado."""
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(db, "verify_email", payload.email, 3, timedelta(hours=1)) or is_rate_limited(db, "verify_ip", client_ip, 10, timedelta(hours=1)):
        raise HTTPException(status_code=429, detail="Muitas solicitações. Tente novamente mais tarde.")
    record_auth_attempt(db, "verify_email", payload.email)
    record_auth_attempt(db, "verify_ip", client_ip)
    user = db.query(User).filter(User.email == payload.email, User.email_verified_at.is_(None)).first()
    if user is not None:
        token = create_account_token(db, user, "verify_email", timedelta(hours=24))
        link = _account_action_url("verify", token)
        try:
            send_account_email(user.email, "Confirme sua conta Amazonia", f"Confirme seu e-mail em até 24 horas:\n{link}")
        except HTTPException:
            logger.exception("Falha ao entregar e-mail de confirmação.")
    return {"message": "Se houver uma conta pendente para esse endereço, enviaremos uma nova confirmação."}


@app.post("/api/v1/auth/forgot-password", status_code=202, tags=["autenticacao"])
def forgot_password(payload: EmailAddressRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    """Solicita recuperação sem revelar a existência da conta."""
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(db, "reset_email", payload.email, 3, timedelta(hours=1)) or is_rate_limited(db, "reset_ip", client_ip, 10, timedelta(hours=1)):
        raise HTTPException(status_code=429, detail="Muitas solicitações. Tente novamente mais tarde.")
    record_auth_attempt(db, "reset_email", payload.email)
    record_auth_attempt(db, "reset_ip", client_ip)
    user = db.query(User).filter(User.email == payload.email, User.email_verified_at.is_not(None)).first()
    if user is not None:
        token = create_account_token(db, user, "password_reset", timedelta(minutes=30))
        link = _account_action_url("reset", token)
        try:
            send_account_email(user.email, "Redefina sua senha Amazonia", f"Este link expira em 30 minutos e só pode ser usado uma vez:\n{link}")
        except HTTPException:
            logger.exception("Falha ao entregar e-mail de recuperação.")
    return {"message": "Se a conta existir e estiver confirmada, enviaremos instruções de recuperação."}


@app.post("/api/v1/auth/reset-password", status_code=200, tags=["autenticacao"])
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    """Redefine a senha com token único e revoga todas as sessões anteriores."""
    user = consume_account_token(db, payload.token, "password_reset")
    if user is None:
        db.rollback()
        raise HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite uma nova recuperação.")
    user.password_hash = hash_password(payload.password)
    user.session_version += 1
    db.commit()
    return {"message": "Senha redefinida. Entre novamente com sua nova senha."}


@app.post("/api/v1/auth/login", response_model=AuthResponse, tags=["autenticacao"])
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    """Autentica sem enumerar contas e aplica limites persistentes por e-mail e IP."""
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(db, "login_email", payload.email, 5, timedelta(minutes=15)) or is_rate_limited(db, "login_ip", client_ip, 20, timedelta(minutes=15)):
        raise HTTPException(status_code=429, detail="Muitas tentativas de acesso. Aguarde antes de tentar novamente.")
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash) or (_verification_required() and user.email_verified_at is None):
        record_auth_attempt(db, "login_email", payload.email)
        record_auth_attempt(db, "login_ip", client_ip)
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    clear_auth_attempts(db, "login_email", payload.email)
    clear_auth_attempts(db, "login_ip", client_ip)
    csrf_token = set_session_cookies(response, user.id, user.session_version)
    return {"user": user, "csrf_token": csrf_token}


@app.post("/api/v1/auth/logout", status_code=204, tags=["autenticacao"])
def logout(response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Response:
    """Revoga todas as sessões emitidas para a conta e remove os cookies."""
    current_user.session_version += 1
    db.commit()
    clear_session_cookies(response)
    response.status_code = 204
    return response


@app.get("/api/v1/auth/me", response_model=UserRead, tags=["autenticacao"])
def current_account(current_user: User = Depends(get_current_user)) -> User:
    """Retorna somente os dados públicos da conta autenticada."""
    return current_user


@app.get("/api/v1/campaigns", response_model=list[CampaignRead], tags=["campanhas"])
def list_campaigns(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Campaign]:
    """Lista exclusivamente campanhas pertencentes à conta autenticada."""
    return db.query(Campaign).filter(Campaign.user_id == current_user.id).order_by(Campaign.updated_at.desc()).all()


def _owned_campaign(db: Session, campaign_id: str, user_id: str) -> Campaign:
    """Oculta campanhas inexistentes e alheias com a mesma resposta 404."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.user_id == user_id).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    return campaign


@app.post("/api/v1/campaigns", response_model=CampaignRead, status_code=201, tags=["campanhas"])
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Campaign:
    """Cria uma campanha sem personagem; o personagem é cadastrado em etapa própria."""
    campaign = Campaign(name=payload.name.strip(), user_id=current_user.id)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@app.get("/api/v1/campaigns/{campaign_id}", response_model=CampaignRead, tags=["campanhas"])
def get_campaign(campaign_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Campaign:
    """Carrega campanha persistida ou retorna 404."""
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    return campaign


@app.post(
    "/api/v1/campaigns/{campaign_id}/character",
    response_model=CharacterRead,
    status_code=201,
    tags=["personagens"],
)
def create_character(
    campaign_id: str,
    payload: CharacterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Character:
    """Cria um único personagem e aplica o pacote da origem escolhida."""
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    if campaign.character is not None:
        raise HTTPException(status_code=409, detail="Esta campanha já possui um personagem.")

    profile = ORIGINS[payload.origin]
    character = Character(
        campaign_id=campaign.id,
        name=payload.name.strip(),
        origin=profile.id.value,
        attributes=payload.attributes.model_dump(),
        skills=dict(profile.starting_skills),
        inventory=list(profile.starting_items),
        needs={"hunger": 0, "thirst": 0, "fatigue": 0, "health": 100},
        position_q=0,
        position_r=0,
        discovered_cells=["0:0"],
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@app.post("/api/v1/campaigns/{campaign_id}/rest", tags=["sobrevivencia"])
def rest_character(campaign_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, object]:
    """Descansa uma hora, recuperando fadiga e avançando o relógio."""
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    character = campaign.character
    if character is None:
        raise HTTPException(status_code=409, detail="Crie o personagem antes de descansar.")

    character.needs = apply_rest_needs(character.needs)
    campaign.world_time_minutes += 60
    db.commit()
    db.refresh(campaign)
    db.refresh(character)
    return {
        "needs": character.needs,
        "world_time_minutes": campaign.world_time_minutes,
        "rest_minutes": 60,
    }


@app.get("/api/v1/game/items", tags=["inventario"])
def list_items() -> list[dict[str, object]]:
    """Lista os itens consumíveis conhecidos pelo protótipo."""
    return [
        {
            "id": item.id,
            "label": item.label,
            "description": item.description,
            "hunger_recovery": item.hunger_recovery,
            "thirst_recovery": item.thirst_recovery,
            "time_cost_minutes": item.time_cost_minutes,
        }
        for item in ITEMS.values()
    ]


@app.post("/api/v1/campaigns/{campaign_id}/inventory/use", tags=["inventario"])
def use_inventory_item(
    campaign_id: str,
    payload: UseItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Consome uma unidade do inventário e persiste seus efeitos atomicamente."""
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    character = campaign.character
    if character is None:
        raise HTTPException(status_code=409, detail="Crie o personagem antes de usar itens.")

    try:
        inventory, needs, time_cost = consume_item(
            list(character.inventory or []),
            dict(character.needs or {}),
            payload.item_id,
        )
    except InventoryRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    character.inventory = inventory
    character.needs = needs
    campaign.world_time_minutes += time_cost
    db.commit()
    db.refresh(campaign)
    db.refresh(character)
    return {
        "inventory": character.inventory,
        "needs": character.needs,
        "world_time_minutes": campaign.world_time_minutes,
        "consumed_item": payload.item_id,
        "time_cost_minutes": time_cost,
    }


def _visible_points_of_interest(db: Session, character: Character) -> list[PointOfInterest]:
    """Busca somente POIs associados às células já descobertas pelo personagem."""
    discovered_positions = []
    for key in character.discovered_cells or []:
        try:
            q_value, r_value = (int(part) for part in key.split(":", maxsplit=1))
        except (ValueError, TypeError):
            continue
        discovered_positions.append(and_(
            PointOfInterest.cell_q == q_value,
            PointOfInterest.cell_r == r_value,
        ))
    if not discovered_positions:
        return []
    return db.query(PointOfInterest).filter(or_(*discovered_positions)).all()


@app.get("/api/v1/campaigns/{campaign_id}/map", tags=["exploracao"])
def get_campaign_map(campaign_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, object]:
    """Retorna a grade hexagonal visível e somente o estado descoberto."""
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    if campaign.character is None:
        raise HTTPException(status_code=409, detail="Crie o personagem antes de explorar.")
    return build_map_data(campaign, campaign.character, _visible_points_of_interest(db, campaign.character))


@app.post("/api/v1/campaigns/{campaign_id}/move", tags=["exploracao"])
def move_character(
    campaign_id: str,
    payload: MoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Move exatamente uma célula adjacente e avança tempo e necessidades."""
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    character = campaign.character
    if character is None:
        raise HTTPException(status_code=409, detail="Crie o personagem antes de explorar.")

    if abs(payload.target_q) > MAX_CELL_COORDINATE or abs(payload.target_r) > MAX_CELL_COORDINATE:
        raise HTTPException(status_code=422, detail="Destino fora dos limites do protótipo.")
    distance = hex_distance(
        character.position_q,
        character.position_r,
        payload.target_q,
        payload.target_r,
    )
    if distance == 0:
        raise HTTPException(status_code=409, detail="O personagem já está nessa célula.")
    if distance != 1:
        raise HTTPException(status_code=422, detail="Só é permitido mover para uma célula adjacente.")

    character.position_q = payload.target_q
    character.position_r = payload.target_r
    character.needs = apply_movement_needs(character.needs)
    discovered = set(character.discovered_cells or [])
    discovered.add(cell_key(payload.target_q, payload.target_r))
    character.discovered_cells = sorted(discovered)
    campaign.world_time_minutes += MOVE_COST_MINUTES
    db.commit()
    db.refresh(campaign)
    db.refresh(character)
    return build_map_data(campaign, character, _visible_points_of_interest(db, character))
