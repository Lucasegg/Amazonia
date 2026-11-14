"""Contratos validados de entrada e saída."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
Profession = Literal["firefighter", "healthcare", "mechanic"]

class CampaignCreate(BaseModel):
    """Dados para iniciar campanha."""
    campaign_name: str = Field(min_length=1, max_length=80)
    character_name: str = Field(min_length=1, max_length=60)
    profession: Profession

class CampaignRead(BaseModel):
    """Ficha pública de uma campanha salva."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    character_name: str
    profession: Profession
    attributes: dict[str, int]
    skills: dict[str, int]
    health: int
    hunger: int
    thirst: int
    fatigue: int
    created_at: datetime

class RollRequest(BaseModel):
    """Parâmetros de teste; o dado é gerado no servidor."""
    attribute: Literal["vigor", "coordination", "perception", "reasoning", "presence"]
    attribute_value: int = Field(ge=1, le=5)
    skill_level: int = Field(ge=0, le=5)
    difficulty: int = Field(ge=1, le=30)
    situational_modifier: int = Field(default=0, ge=-2, le=2)

class RollRead(BaseModel):
    """Resultado mecânico do teste."""
    die: int
    attribute_modifier: int
    skill_level: int
    situational_modifier: int
    total: int
    difficulty: int
    outcome: Literal["failure", "success", "strong_success", "complication"]
