"""API do jogo; o cliente nunca decide resultados mecânicos nem movimento."""
import os
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
from app.schemas import AuthResponse, CampaignCreate, CampaignRead, CharacterCreate, CharacterRead, LoginRequest, MoveRequest, RegisterRequest, UseItemRequest, UserRead
from app.auth import clear_session_cookies, get_current_user, hash_password, set_session_cookies, verify_password

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


@app.post("/api/v1/auth/register", response_model=AuthResponse, status_code=201, tags=["autenticacao"])
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    """Cria uma conta com senha derivada por Argon2id e inicia sessão."""
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
    set_session_cookies(response, user.id)\n    return {"user": user}


@app.post("/api/v1/auth/login", response_model=AuthResponse, tags=["autenticacao"])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    """Autentica por e-mail e senha sem revelar qual campo falhou."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.", headers={"WWW-Authenticate": "Bearer"})
    set_session_cookies(response, user.id)\n    return {"user": user}


@app.post("/api/v1/auth/logout", status_code=204, tags=["autenticacao"])
def logout(response: Response) -> Response:
    """Encerra a sessão removendo os cookies do navegador."""
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
