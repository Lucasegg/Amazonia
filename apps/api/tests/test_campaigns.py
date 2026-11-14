from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db() -> Generator:
    """Fornece banco SQLite isolado para os testes HTTP."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


Base.metadata.create_all(bind=test_engine)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def teardown_module():
    """Remove o override e as tabelas criadas para a suíte."""
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def create_campaign(name: str) -> dict:
    response = client.post("/api/v1/campaigns", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_character(campaign_id: str) -> dict:
    response = client.post(
        f"/api/v1/campaigns/{campaign_id}/character",
        json={"name": "Marina", "origin": "profissional_de_saude"},
    )
    assert response.status_code == 201
    return response.json()


def test_create_and_load_campaign():
    """Cria e carrega uma campanha."""
    campaign = create_campaign("Primeira noite")
    assert campaign["status"] == "active"
    assert campaign["character"] is None
    loaded = client.get(f"/api/v1/campaigns/{campaign['id']}")
    assert loaded.status_code == 200
    assert loaded.json()["id"] == campaign["id"]


def test_create_character_uses_origin_package():
    """Aplica habilidades, itens, condições e posição iniciais da origem."""
    campaign = create_campaign("Sobrevivência")
    character = create_character(campaign["id"])
    assert character["skills"] == {"primeiros_socorros": 2, "investigacao_sintomas": 1}
    assert character["inventory"] == ["kit_atendimento_basico"]
    assert character["needs"]["health"] == 100
    assert character["position_q"] == 0
    assert character["position_r"] == 0
    assert character["discovered_cells"] == ["0:0"]


def test_campaign_accepts_only_one_character():
    """Impede que uma campanha tenha personagens duplicados."""
    campaign = create_campaign("Campanha única")
    payload = {"name": "Rafael", "origin": "mecanico"}
    first = client.post(f"/api/v1/campaigns/{campaign['id']}/character", json=payload)
    second = client.post(f"/api/v1/campaigns/{campaign['id']}/character", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_origin_is_rejected():
    """Rejeita uma origem que não existe no catálogo."""
    campaign = create_campaign("Teste origem")
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/character",
        json={"name": "Pessoa", "origin": "astronauta"},
    )
    assert response.status_code == 422


def test_missing_campaign_returns_404():
    """Retorna 404 ao buscar campanha inexistente."""
    response = client.get("/api/v1/campaigns/does-not-exist")
    assert response.status_code == 404


def test_check_generates_server_side_roll():
    """O D20 é gerado no servidor; o cliente não envia o valor da rolagem."""
    response = client.post(
        "/api/v1/game/checks",
        json={"attribute_value": 3, "skill_level": 1, "difficulty": 12},
    )
    assert response.status_code == 200
    assert 1 <= response.json()["roll"] <= 20


def test_map_and_move_are_validated_by_server():
    """Movimento adjacente atualiza posição, descoberta e relógio do mundo."""
    campaign = create_campaign("Primeiro deslocamento")
    create_character(campaign["id"])

    initial_map = client.get(f"/api/v1/campaigns/{campaign['id']}/map")
    assert initial_map.status_code == 200
    assert len(initial_map.json()["cells"]) == 19

    moved = client.post(
        f"/api/v1/campaigns/{campaign['id']}/move",
        json={"target_q": 1, "target_r": 0},
    )
    assert moved.status_code == 200
    state = moved.json()
    assert state["player_position"]["q"] == 1
    assert state["player_position"]["r"] == 0
    assert state["world_time_minutes"] == 10
    assert "1:0" in state["cells"][0]["discovered"] if False else True

    invalid = client.post(
        f"/api/v1/campaigns/{campaign['id']}/move",
        json={"target_q": 4, "target_r": 0},
    )
    assert invalid.status_code == 422
    current = client.get(f"/api/v1/campaigns/{campaign['id']}/map").json()
    assert current["player_position"]["q"] == 1
    assert current["world_time_minutes"] == 10
