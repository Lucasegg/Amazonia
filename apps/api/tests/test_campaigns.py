from collections.abc import Generator
from uuid import uuid4

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


def create_playable_campaign(name: str = "Campanha de teste") -> tuple[dict, dict]:
    """Cria campanha e personagem para os testes de jogo."""
    campaign_response = client.post("/api/v1/campaigns", json={"name": name})
    assert campaign_response.status_code == 201
    campaign = campaign_response.json()
    character_response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/character",
        json={"name": "Marina", "origin": "bombeiro"},
    )
    assert character_response.status_code == 201
    return campaign, character_response.json()


def test_create_and_load_campaign():
    """Cria e carrega uma campanha."""
    created = client.post("/api/v1/campaigns", json={"name": "Primeira noite"})
    assert created.status_code == 201
    campaign = created.json()
    assert campaign["name"] == "Primeira noite"
    assert campaign["status"] == "active"
    assert campaign["character"] is None
    loaded = client.get(f"/api/v1/campaigns/{campaign['id']}")
    assert loaded.status_code == 200
    assert loaded.json()["id"] == campaign["id"]


def test_create_character_uses_origin_package():
    """Aplica habilidades, itens e condições iniciais da profissão."""
    campaign = client.post("/api/v1/campaigns", json={"name": "Sobrevivência"}).json()
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/character",
        json={"name": "Marina", "origin": "profissional_de_saude"},
    )
    assert response.status_code == 201
    character = response.json()
    assert character["skills"] == {"primeiros_socorros": 2, "investigacao_sintomas": 1}
    assert character["inventory"] == ["kit_atendimento_basico"]
    assert character["needs"]["health"] == 100


def test_campaign_accepts_only_one_character():
    """Impede que uma campanha tenha personagens duplicados."""
    campaign = client.post("/api/v1/campaigns", json={"name": "Campanha única"}).json()
    payload = {"name": "Rafael", "origin": "mecanico"}
    first = client.post(f"/api/v1/campaigns/{campaign['id']}/character", json=payload)
    second = client.post(f"/api/v1/campaigns/{campaign['id']}/character", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_origin_is_rejected():
    """Rejeita uma origem que não existe no catálogo."""
    campaign = client.post("/api/v1/campaigns", json={"name": "Teste origem"}).json()
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


def test_map_hides_undiscovered_locations():
    """O mapa revela apenas o ponto inicial conhecido."""
    campaign, character = create_playable_campaign("Mapa sem spoilers")
    response = client.get(f"/api/v1/campaigns/{campaign['id']}/map")
    assert response.status_code == 200
    data = response.json()
    assert data["current_position"]["location_id"] == "praca_se"
    assert [item["id"] for item in data["known_locations"]] == ["praca_se"]
    assert character["position"]["location_id"] == "praca_se"


def test_search_discovers_nearest_poi_and_is_idempotent():
    """Busca revela o ponto próximo e repetição da mesma chave não avança o tempo."""
    campaign, _ = create_playable_campaign("Descoberta idempotente")
    key = str(uuid4())
    payload = {"action": "search", "idempotency_key": key}
    first = client.post(f"/api/v1/campaigns/{campaign['id']}/actions", json=payload)
    second = client.post(f"/api/v1/campaigns/{campaign['id']}/actions", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["event_id"] == second.json()["event_id"]
    assert first.json()["location"]["id"] == "pateo_do_colegio"
    assert first.json()["world_time_minutes"] == 15
    assert second.json()["world_time_minutes"] == 15
    events = client.get(f"/api/v1/campaigns/{campaign['id']}/events")
    assert events.status_code == 200
    assert len(events.json()) == 1


def test_move_requires_discovered_location_and_advances_world_time():
    """Deslocamento só aceita local descoberto e atualiza posição/tempo."""
    campaign, _ = create_playable_campaign("Movimentação")
    hidden = client.post(
        f"/api/v1/campaigns/{campaign['id']}/actions",
        json={"action": "move", "target_location_id": "masp", "idempotency_key": str(uuid4())},
    )
    assert hidden.status_code == 404

    discovered = client.post(
        f"/api/v1/campaigns/{campaign['id']}/actions",
        json={"action": "search", "idempotency_key": str(uuid4())},
    ).json()
    target_id = discovered["location"]["id"]
    moved = client.post(
        f"/api/v1/campaigns/{campaign['id']}/actions",
        json={"action": "move", "target_location_id": target_id, "idempotency_key": str(uuid4())},
    )
    assert moved.status_code == 200
    assert moved.json()["current_position"]["location_id"] == target_id
    assert moved.json()["world_time_minutes"] > discovered["world_time_minutes"]


def test_search_without_nearby_undiscovered_poi_returns_conflict():
    """Busca sem novo ponto no raio não altera a campanha."""
    campaign, _ = create_playable_campaign("Busca sem alvo")
    for _ in range(5):
        result = client.post(
            f"/api/v1/campaigns/{campaign['id']}/actions",
            json={"action": "search", "idempotency_key": str(uuid4())},
        )
        if result.status_code == 409:
            break
        assert result.status_code == 200
    assert result.status_code == 409
