"""API inicial do jogo; regras e estado do mundo são controlados pelo servidor."""
import os
from math import ceil
from random import SystemRandom
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.rules import ORIGINS, Origin, RuleValidationError, resolve_check
from app.models import Campaign, Character, WorldEvent
from app.schemas import (
    ActionRead,
    ActionRequest,
    CampaignCreate,
    CampaignRead,
    CharacterCreate,
    CharacterRead,
    MapRead,
    WorldEventRead,
)
from app.world import (
    LOCATIONS,
    SEARCH_ACTION_MINUTES,
    SEARCH_RADIUS_KM,
    SPAWN_LOCATION_ID,
    SPAWN_POSITION,
    distance_km,
    map_payload,
    travel_minutes,
)

app = FastAPI(
    title="Amazonia API",
    version="0.4.0",
    description="API do RPG Amazonia com regras determinísticas e estado do mundo persistido.",
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
    """Cria personagem, aplica origem e define o spawn fictício do protótipo."""
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
        position=dict(SPAWN_POSITION),
        discovered_locations=[SPAWN_LOCATION_ID],
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@app.get("/api/v1/campaigns/{campaign_id}/map", response_model=MapRead, tags=["exploracao"])
def get_campaign_map(campaign_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    """Retorna posição e somente os pontos de interesse descobertos."""
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    if campaign.character is None:
        raise HTTPException(status_code=409, detail="Crie um personagem antes de abrir o mapa.")
    return map_payload(campaign.id, campaign.world_time_minutes, campaign.character)


@app.post(
    "/api/v1/campaigns/{campaign_id}/actions",
    response_model=ActionRead,
    tags=["exploracao"],
)
def perform_world_action(
    campaign_id: str,
    payload: ActionRequest,
    db: Session = Depends(get_db),
) -> ActionRead:
    """Executa busca ou deslocamento, atualizando mundo e evento em uma transação."""
    key = str(payload.idempotency_key)
    existing = (
        db.query(WorldEvent)
        .filter(WorldEvent.campaign_id == campaign_id, WorldEvent.idempotency_key == key)
        .first()
    )
    if existing is not None:
        return ActionRead(**existing.payload)

    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    character = campaign.character
    if character is None:
        raise HTTPException(status_code=409, detail="Crie um personagem antes de explorar.")

    current_lat = float(character.position["latitude"])
    current_lon = float(character.position["longitude"])
    location_data: dict[str, object]
    if payload.action == "search":
        known = set(character.discovered_locations)
        candidates = []
        for location_id, location in LOCATIONS.items():
            if location_id in known:
                continue
            distance = distance_km(
                current_lat,
                current_lon,
                float(location["latitude"]),
                float(location["longitude"]),
            )
            if distance <= SEARCH_RADIUS_KM:
                candidates.append((distance, location_id, location))
        if not candidates:
            raise HTTPException(
                status_code=409,
                detail="Não há novos pontos de interesse próximos para descobrir.",
            )
        distance, location_id, location = min(candidates, key=lambda item: item[0])
        character.discovered_locations = [*character.discovered_locations, location_id]
        campaign.world_time_minutes += SEARCH_ACTION_MINUTES
        location_data = dict(location)
        location_data["distance_km"] = round(distance, 2)
        message = f"Você encontrou {location['name']} durante a busca nos arredores."
    else:
        location_id = payload.target_location_id
        if not location_id:
            raise HTTPException(status_code=422, detail="Informe o local de destino.")
        if location_id not in character.discovered_locations:
            raise HTTPException(status_code=404, detail="Esse local ainda não foi descoberto.")
        location = LOCATIONS.get(location_id)
        if location is None:
            raise HTTPException(status_code=404, detail="Local de destino não encontrado.")
        if location_id == character.position.get("location_id"):
            raise HTTPException(status_code=409, detail="Você já está nesse local.")
        distance = distance_km(
            current_lat,
            current_lon,
            float(location["latitude"]),
            float(location["longitude"]),
        )
        campaign.world_time_minutes += travel_minutes(distance)
        character.position = {
            "location_id": location_id,
            "latitude": float(location["latitude"]),
            "longitude": float(location["longitude"]),
        }
        location_data = dict(location)
        location_data["distance_km"] = 0.0
        message = f"Você chegou a {location['name']}."

    event_id = str(uuid4())
    result = ActionRead(
        event_id=event_id,
        action=payload.action,
        message=message,
        world_time_minutes=campaign.world_time_minutes,
        current_position=dict(character.position),
        location=location_data,
    )
    event = WorldEvent(
        id=event_id,
        campaign_id=campaign.id,
        character_id=character.id,
        idempotency_key=key,
        event_type=payload.action,
        world_time_minutes=campaign.world_time_minutes,
        payload=result.model_dump(mode="json"),
    )
    db.add(event)
    db.add(campaign)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        repeated = (
            db.query(WorldEvent)
            .filter(WorldEvent.campaign_id == campaign_id, WorldEvent.idempotency_key == key)
            .first()
        )
        if repeated is not None:
            return ActionRead(**repeated.payload)
        raise
    return result


@app.get(
    "/api/v1/campaigns/{campaign_id}/events",
    response_model=list[WorldEventRead],
    tags=["exploracao"],
)
def list_world_events(campaign_id: str, db: Session = Depends(get_db)) -> list[WorldEvent]:
    """Lista os últimos eventos da campanha em ordem cronológica."""
    if db.get(Campaign, campaign_id) is None:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    return (
        db.query(WorldEvent)
        .filter(WorldEvent.campaign_id == campaign_id)
        .order_by(WorldEvent.world_time_minutes, WorldEvent.created_at)
        .limit(100)
        .all()
    )
