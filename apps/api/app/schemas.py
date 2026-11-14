"""Contratos HTTP para contas, campanhas, personagens e movimentação."""
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

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

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
