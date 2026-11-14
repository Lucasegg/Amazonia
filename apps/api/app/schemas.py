"""Contratos HTTP para campanhas, personagens e exploração."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.rules import Origin


class CampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class CharacterAttributes(BaseModel):
    vigor: int = Field(default=3, ge=1, le=5)
    coordenacao: int = Field(default=3, ge=1, le=5)
    percepcao: int = Field(default=3, ge=1, le=5)
    raciocinio: int = Field(default=3, ge=1, le=5)
    presenca: int = Field(default=3, ge=1, le=5)


class CharacterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    origin: Origin
    attributes: CharacterAttributes = Field(default_factory=CharacterAttributes)


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    name: str
    origin: str
    attributes: dict[str, int]
    skills: dict[str, int]
    inventory: list[str]
    needs: dict[str, int]


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    world_time_minutes: int
    character: CharacterRead | None = None


class LocationRead(BaseModel):
    """Local geográfico conhecido pelo personagem."""

    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    description: str
    distance_km: float


class MapRead(BaseModel):
    """Mapa limitado aos locais que o personagem já descobriu."""

    campaign_id: str
    world_time_minutes: int
    current_position: dict[str, object]
    known_locations: list[LocationRead]


class ActionRequest(BaseModel):
    """Comando de exploração com chave de idempotência obrigatória."""

    action: Literal["search", "move"]
    idempotency_key: UUID
    target_location_id: str | None = Field(default=None, min_length=2, max_length=80)


class ActionRead(BaseModel):
    """Resultado autoritativo de uma ação de exploração."""

    event_id: str
    action: Literal["search", "move"]
    message: str
    world_time_minutes: int
    current_position: dict[str, object]
    location: LocationRead | None = None


class WorldEventRead(BaseModel):
    """Evento persistido da campanha."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    world_time_minutes: int
    payload: dict[str, object]
    created_at: datetime
