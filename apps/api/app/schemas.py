"""Contratos HTTP para contas, campanhas, personagens e movimentação."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.domain.rules import Origin

class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=12, max_length=128)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Informe um e-mail válido.")
        return normalized

class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    role: str

class AuthResponse(BaseModel):
    user: UserRead
    csrf_token: str

class CampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)

class CharacterAttributes(BaseModel):
    vigor: int = Field(default=3, ge=1, le=5)
    coordenacao: int = Field(default=3, ge=1, le=5)
    percepcao: int = Field(default=3, ge=1, le=5)
    raciocinio: int = Field(default=3, ge=1, le=5)
    presenca: int = Field(default=3, ge=1, le=5)

class CharacterAppearance(BaseModel):
    hair_style: Literal["curto", "longo", "raspado", "cacheado", "trancas"] = "curto"
    hair_color: Literal["preto", "castanho", "loiro", "ruivo", "grisalho"] = "preto"
    eye_color: Literal["castanho", "preto", "azul", "verde", "mel"] = "castanho"
    skin_tone: Literal["claro", "medio", "escuro"] = "medio"
    tattoo_style: Literal["nenhuma", "minimalista", "geometrica", "tradicional"] = "nenhuma"
    tattoo_placement: Literal["nenhuma", "braco", "antebraco", "ombro", "pescoco"] = "nenhuma"
    tattoo_scale: Literal["pequena", "media", "grande"] = "pequena"
    shirt_model: Literal["camiseta", "regata", "manga_longa", "jaqueta"] = "camiseta"
    shirt_color: Literal["preta", "cinza", "azul", "verde", "vermelha", "bege"] = "cinza"
    pants_model: Literal["jeans", "cargo", "tatico", "bermuda"] = "cargo"
    pants_color: Literal["preta", "azul", "verde", "marrom", "bege"] = "verde"


class CharacterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    origin: Origin
    attributes: CharacterAttributes = Field(default_factory=CharacterAttributes)
    appearance: CharacterAppearance = Field(default_factory=CharacterAppearance)

class MoveRequest(BaseModel):
    target_q: int = Field(ge=-50, le=50)
    target_r: int = Field(ge=-50, le=50)

class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campaign_id: str
    name: str
    origin: str
    attributes: dict[str, int]
    appearance: dict[str, str]
    skills: dict[str, int]
    inventory: list[str]
    needs: dict[str, int]
    position_q: int
    position_r: int
    discovered_cells: list[str]

class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    status: str
    world_time_minutes: int
    character: CharacterRead | None = None

class UseItemRequest(BaseModel):
    item_id: str = Field(min_length=1, max_length=80)


class AccountTokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=12, max_length=128)


class EmailAddressRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Informe um e-mail válido.")
        return normalized
