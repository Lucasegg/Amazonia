"""Testes HTTP com SQLite em memória isolado."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def override_get_db():
    """Fornece banco isolado e limpa tabelas após o teste."""
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
    """Campanha deve persistir e retornar a ficha de origem."""
    response = client.post("/api/v1/campaigns", json={"campaign_name":"Primeira noite","character_name":"Ana","profession":"mechanic"})
    assert response.status_code == 201
    data = response.json()
    assert data["skills"]["mechanics"] == 2
    assert client.get("/api/v1/campaigns/" + data["id"]).json()["character_name"] == "Ana"

def test_missing_campaign_returns_404() -> None:
    """Campanha inexistente retorna 404."""
    assert client.get("/api/v1/campaigns/not-found").status_code == 404

def test_professions_catalog() -> None:
    """Catálogo contém exatamente as três origens do protótipo."""
    response = client.get("/api/v1/professions")
    assert {item["id"] for item in response.json()} == {"firefighter", "healthcare", "mechanic"}
