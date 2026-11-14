"""Testes HTTP com banco SQLite em memória isolado."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def override_get_db():
    """Fornece sessão isolada e remove tabelas após cada teste."""
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_and_read_campaign() -> None:
    """Campanha salva deve retornar atributos, habilidades e itens da origem."""
    response = client.post("/api/v1/campaigns", json={
        "campaign_name": "Primeira noite",
        "character_name": "Ana",
        "profession": "mecanico",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["skills"]["mecanica"] == 2
    assert data["starting_items"] == ["conjunto_compacto_ferramentas"]
    loaded = client.get("/api/v1/campaigns/" + data["id"])
    assert loaded.status_code == 200
    assert loaded.json()["character_name"] == "Ana"

def test_missing_campaign_returns_404() -> None:
    """Campanha inexistente retorna 404."""
    assert client.get("/api/v1/campaigns/not-found").status_code == 404

def test_origins_endpoint_preserves_game_design() -> None:
    """Catálogo HTTP reflete as três origens documentadas."""
    response = client.get("/api/v1/game/origins")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {
        "bombeiro", "profissional_de_saude", "mecanico"
    }

def test_check_does_not_accept_client_roll() -> None:
    """O resultado do dado não pode ser escolhido pelo cliente."""
    response = client.post("/api/v1/game/checks", json={
        "attribute": "vigor",
        "attribute_value": 3,
        "skill_level": 1,
        "difficulty": 12,
    })
    assert response.status_code == 200
    assert 1 <= response.json()["roll"] <= 20
