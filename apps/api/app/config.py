"""Configurações tipadas da aplicação."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Lê configurações e segredos exclusivamente do ambiente."""
    app_name: str = "Amazonia API"
    environment: str = "development"
    database_url: str
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        """Converte origens CORS separadas por vírgula em lista."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações cacheadas do processo."""
    return Settings()
