"""Contratos validados de entrada e saída da API."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Profession = Literal["bombeiro", "profissional_de_saude", "mecanico"]
Attribute = Literal["vigor", "coordenacao", "percepcao", "raciocinio", "presenca"]

class CampaignCreate(BaseModel):
    """Dados mínimos para iniciar campanha e personagem."""
    campaign_name: str = Field(min_length=1, max_length=80)
    character_name: str = Field(min_length=1, max_length=60)
    profession: Profession

class CampaignRead(BaseModel):
    """Estado público persistido da campanha."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    character_name: str
    profession: Profession
    attributes: dict[str, int]
    skills: dict[str, int]
    starting_items: list[str]
    contextual_strength: str
    health: int
    hunger: int
    thirst: int
    fatigue: int
    created_at: datetime

class RollRequest(BaseModel):
    """Parâmetros de teste; o servidor gera o resultado do D20."""
    attribute: Attribute
    attribute_value: int = Field(ge=1, le=5)
    skill_level: int = Field(ge=0, le=5)
    difficulty: int = Field(ge=1, le=30)
    situational_modifier: int = Field(default=0, ge=-2, le=2)

class RollRead(BaseModel):
    """Resultado mecânico calculado no servidor."""
    roll: int
    attribute_modifier: int
    skill_level: int
    situational_modifier: int
    total: int
    difficulty: int
    success: bool
    margin: int
    outcome: str
