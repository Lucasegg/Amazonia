import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.rules import ORIGINS, Origin, RuleValidationError, resolve_check
from app.models import Campaign, Character
from app.schemas import CampaignCreate, CampaignRead, CharacterCreate, CharacterRead

app = FastAPI(
    title="Amazonia API",
    version="0.2.0",
    description="API inicial do RPG Amazonia. O motor de regras é determinístico e independente da IA.",
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
    roll: int = Field(ge=1, le=20)
    attribute_value: int = Field(ge=1, le=5)
    skill_level: int = Field(ge=0, le=5)
    difficulty: int
    situational_modifier: int = Field(default=0, ge=-2, le=2)


@app.get("/health", tags=["operacao"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "amazonia-api"}


@app.get("/api/v1/game/origins", tags=["jogo"])
def list_origins() -> list[dict[str, object]]:
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
    try:
        result = resolve_check(**payload.model_dump())
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
    campaign = Campaign(name=payload.name.strip())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@app.get("/api/v1/campaigns/{campaign_id}", response_model=CampaignRead, tags=["campanhas"])
def get_campaign(campaign_id: str, db: Session = Depends(get_db)) -> Campaign:
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
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character
