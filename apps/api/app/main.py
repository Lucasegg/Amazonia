from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.domain.rules import ORIGINS, Origin, RuleValidationError, resolve_check

app = FastAPI(
    title="Amazonia API",
    version="0.1.0",
    description="API inicial do RPG Amazonia. O motor de regras é determinístico e independente da IA.",
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
