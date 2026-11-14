from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401
from app.models import PointOfInterest


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
    assert character["inventory"] == ["kit_atendimento_basico", "agua_potavel", "racao"]
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
    assert state["character_needs"] == {"hunger": 1, "thirst": 2, "fatigue": 1, "health": 100}
    persisted = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert persisted["character"]["needs"] == state["character_needs"]
    target_cell = next(cell for cell in state["cells"] if cell["q"] == 1 and cell["r"] == 0)
    assert target_cell["discovered"] is True
    assert target_cell["current"] is True

    invalid = client.post(
        f"/api/v1/campaigns/{campaign['id']}/move",
        json={"target_q": 4, "target_r": 0},
    )
    assert invalid.status_code == 422
    current = client.get(f"/api/v1/campaigns/{campaign['id']}/map").json()
    assert current["player_position"]["q"] == 1
    assert current["world_time_minutes"] == 10



def test_map_reveals_points_of_interest_only_after_cell_discovery():
    """POIs de células vizinhas permanecem ocultos até o personagem explorá-las."""
    campaign = create_campaign("Descoberta de locais")
    create_character(campaign["id"])

    with TestingSessionLocal() as session:
        session.add_all([
            PointOfInterest(
                id="poi-center",
                source_ref="test:center",
                name="Ponto conhecido",
                category="healthcare",
                latitude=-23.5505,
                longitude=-46.6333,
                cell_q=0,
                cell_r=0,
                tags={},
                source="Fixture",
                source_license="CC0",
                source_url="https://example.invalid/",
            ),
            PointOfInterest(
                id="poi-east",
                source_ref="test:east",
                name="Ponto oculto",
                category="food",
                latitude=-23.5505,
                longitude=-46.6238,
                cell_q=1,
                cell_r=0,
                tags={},
                source="Fixture",
                source_license="CC0",
                source_url="https://example.invalid/",
            ),
        ])
        session.commit()

    initial = client.get(f"/api/v1/campaigns/{campaign['id']}/map").json()
    assert [poi["name"] for poi in initial["points_of_interest"]] == ["Ponto conhecido"]

    moved = client.post(
        f"/api/v1/campaigns/{campaign['id']}/move",
        json={"target_q": 1, "target_r": 0},
    )
    assert moved.status_code == 200
    names = {poi["name"] for poi in moved.json()["points_of_interest"]}
    assert names == {"Ponto conhecido", "Ponto oculto"}


def test_consuming_water_persists_inventory_needs_and_world_time():
    campaign = create_campaign("Água para a jornada")
    character = create_character(campaign["id"])
    response = client.post(
        f"/api/v1/campaigns/{campaign['id']}/inventory/use",
        json={"item_id": "agua_potavel"},
    )
    assert response.status_code == 200
    state = response.json()
    assert "agua_potavel" not in state["inventory"]
    assert "racao" in state["inventory"]
    assert state["needs"]["thirst"] == 0
    assert state["world_time_minutes"] == 5

    persisted = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert persisted["character"]["inventory"] == state["inventory"]
    assert persisted["character"]["needs"] == state["needs"]
    assert persisted["world_time_minutes"] == 5


def test_cannot_consume_missing_item_or_unknown_item():
    campaign = create_campaign("Inventário limitado")
    create_character(campaign["id"])

    missing = client.post(
        f"/api/v1/campaigns/{campaign['id']}/inventory/use",
        json={"item_id": "kit_atendimento_basico"},
    )
    assert missing.status_code == 409

    unknown = client.post(
        f"/api/v1/campaigns/{campaign['id']}/inventory/use",
        json={"item_id": "item_que_nao_existe"},
    )
    assert unknown.status_code == 409

    current = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert current["character"]["needs"]["thirst"] == 0
    assert current["world_time_minutes"] == 0


def test_rest_action_recovers_fatigue_and_persists_time():
    campaign = create_campaign("Uma pausa necessária")
    create_character(campaign["id"])
    with TestingSessionLocal() as session:
        stored = session.get(models.Character, client.get(f"/api/v1/campaigns/{campaign['id']}").json()["character"]["id"])
        stored.needs = {"hunger": 10, "thirst": 20, "fatigue": 45, "health": 90}
        session.commit()

    response = client.post(f"/api/v1/campaigns/{campaign['id']}/rest")
    assert response.status_code == 200
    assert response.json()["needs"] == {"hunger": 16, "thirst": 30, "fatigue": 15, "health": 90}
    assert response.json()["world_time_minutes"] == 60

    persisted = client.get(f"/api/v1/campaigns/{campaign['id']}").json()
    assert persisted["character"]["needs"] == response.json()["needs"]
    assert persisted["world_time_minutes"] == 60
