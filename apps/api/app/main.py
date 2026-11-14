"""API HTTP inicial; regras do domínio não dependem da camada web."""
from random import SystemRandom
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.domain.rules import ORIGINS, Origin, RuleValidationError, resolve_check
from app.models import Campaign
from app.schemas import CampaignCreate, CampaignRead, RollRead, RollRequest

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="API inicial do RPG Amazonia.")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
DEFAULT_ATTRIBUTES = {"vigor": 3, "coordenacao": 3, "percepcao": 3, "raciocinio": 3, "presenca": 3}

@app.get("/health", tags=["operacao"])
def health() -> dict[str, str]:
    """Verifica disponibilidade sem expor configuração."""
    return {"status": "ok", "service": "amazonia-api"}

@app.get("/api/v1/game/origins", tags=["jogo"])
def list_origins() -> list[dict[str, object]]:
    """Lista as três origens do primeiro protótipo."""
    return [{"id": p.id.value, "label": p.label, "starting_skills": dict(p.starting_skills), "starting_items": list(p.starting_items), "contextual_strength": p.contextual_strength} for p in ORIGINS.values()]

@app.get("/api/v1/game/origins/{origin_id}", tags=["jogo"])
def get_origin(origin_id: str) -> dict[str, object]:
    """Retorna o pacote de uma origem ou 404."""
    try:
        p = ORIGINS[Origin(origin_id)]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Origem não encontrada.") from exc
    return {"id": p.id.value, "label": p.label, "starting_skills": dict(p.starting_skills), "starting_items": list(p.starting_items), "contextual_strength": p.contextual_strength}

@app.post("/api/v1/game/checks", response_model=RollRead, tags=["jogo"])
def perform_check(payload: RollRequest) -> RollRead:
    """Gera o D20 no servidor e resolve o teste sem aceitar rolagem do cliente."""
    try:
        result = resolve_check(roll=SystemRandom().randint(1, 20), attribute_value=payload.attribute_value, skill_level=payload.skill_level, difficulty=payload.difficulty, situational_modifier=payload.situational_modifier)
    except RuleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RollRead(**result.__dict__)

@app.post("/api/v1/campaigns", response_model=CampaignRead, status_code=201, tags=["campanhas"])
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> Campaign:
    """Cria campanha com ficha, habilidades e itens coerentes com a origem."""
    name, character_name = payload.campaign_name.strip(), payload.character_name.strip()
    if not name or not character_name:
        raise HTTPException(status_code=422, detail="Nome da campanha e personagem são obrigatórios.")
    p = ORIGINS[Origin(payload.profession)]
    campaign = Campaign(name=name, character_name=character_name, profession=p.id.value, attributes=dict(DEFAULT_ATTRIBUTES), skills=dict(p.starting_skills), starting_items=list(p.starting_items), contextual_strength=p.contextual_strength)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

@app.get("/api/v1/campaigns/{campaign_id}", response_model=CampaignRead, tags=["campanhas"])
def get_campaign(campaign_id: str, db: Session = Depends(get_db)) -> Campaign:
    """Carrega campanha persistida ou retorna 404."""
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    return campaign
