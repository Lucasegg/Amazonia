"""API do jogo; o cliente nunca decide resultados mecânicos nem movimento."""
import os
from random import SystemRandom

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.rules import ORIGINS, Origin, RuleValidationError, resolve_check
from app.domain.world import (
    MAX_CELL_COORDINATE,
    MOVE_COST_MINUTES,
    build_map_data,
    cell_key,
    hex_distance,
)
from app.models import Campaign, Character, PointOfInterest
from app.schemas import CampaignCreate, CampaignRead, CharacterCreate, CharacterRead, MoveRequest

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
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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


@app.post("/api/v1/campaigns", response_model=CampaignRead, status_code=201, tags=["campanhas"])
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> Campaign:
    """Cria uma campanha sem personagem; o personagem é cadastrado em etapa própria."""
    campaign = Campaign(name=payload.name.strip())
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
) -> Character:
    """Cria um único personagem e aplica o pacote da origem escolhida."""
    campaign = db.get(Campaign, campaign_id)
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
def get_campaign_map(campaign_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    """Retorna a grade hexagonal visível e somente o estado descoberto."""
    campaign = db.get(Campaign, campaign_id)
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
) -> dict[str, object]:
    """Move exatamente uma célula adjacente e avança o relógio do mundo."""
    campaign = db.get(Campaign, campaign_id)
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
    discovered = set(character.discovered_cells or [])
    discovered.add(cell_key(payload.target_q, payload.target_r))
    character.discovered_cells = sorted(discovered)
    campaign.world_time_minutes += MOVE_COST_MINUTES
    db.commit()
    db.refresh(campaign)
    db.refresh(character)
    return build_map_data(campaign, character, _visible_points_of_interest(db, character))
