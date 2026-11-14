import os
import re
from datetime import datetime, timezone
import pytest
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
import app.main as main_module
from app import models  # noqa: F401
from app.models import AuthAttempt, PointOfInterest, User


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
os.environ["AMAZONIA_AUTH_SECRET"] = "ci-test-secret-not-for-production-000000000000000000000000"
os.environ["AMAZONIA_REQUIRE_EMAIL_VERIFICATION"] = "false"
client = TestClient(app)
registration = client.post("/api/v1/auth/register", json={
    "email": "jogador@example.com",
    "display_name": "Jogador de Teste",
    "password": "Senha-forte-de-teste-2026",
})
assert registration.status_code == 202


@pytest.fixture(autouse=True)
def reset_auth_attempts():
    """Isola contadores de rate limit entre casos da suíte."""
    with TestingSessionLocal() as session:
        session.query(AuthAttempt).delete()
        session.commit()

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
    assert character["appearance"]["hair_style"] == "curto"
    assert character["appearance"]["shirt_model"] == "camiseta"
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


def test_authentication_required_and_campaigns_are_isolated_by_owner():
    """Exige token e impede que outra conta consulte campanha alheia."""
    anonymous = TestClient(app)
    denied = anonymous.post("/api/v1/campaigns", json={"name": "Sem sessão"})
    assert denied.status_code == 401

    owned = create_campaign("Campanha privada")
    second = anonymous.post("/api/v1/auth/register", json={
        "email": "outra-conta@example.com",
        "display_name": "Outra Conta",
        "password": "Outra-senha-forte-2026",
    })
    assert second.status_code == 202

    assert anonymous.get("/api/v1/campaigns").status_code == 200
    assert anonymous.get("/api/v1/campaigns").json() == []
    assert anonymous.get(f"/api/v1/campaigns/{owned['id']}").status_code == 404
    assert anonymous.post(f"/api/v1/campaigns/{owned['id']}/rest").status_code == 404


def test_login_normalizes_email_and_rejects_invalid_password():
    """Aceita e-mail normalizado e não revela credenciais inválidas."""
    response = TestClient(app).post("/api/v1/auth/login", json={
        "email": " JOGADOR@EXAMPLE.COM ",
        "password": "Senha-forte-de-teste-2026",
    })
    assert response.status_code == 200
    invalid = TestClient(app).post("/api/v1/auth/login", json={
        "email": "jogador@example.com",
        "password": "senha-incorreta",
    })
    assert invalid.status_code == 401


def test_second_account_cannot_access_character_map_inventory_or_movement():
    """Todas as operações de personagem respeitam o proprietário da campanha."""
    owner_campaign = create_campaign("Dados privados do primeiro jogador")
    create_character(owner_campaign["id"])

    second_client = TestClient(app)
    second = second_client.post("/api/v1/auth/register", json={
        "email": "isolamento@example.com",
        "display_name": "Conta Isolada",
        "password": "Senha-forte-isolamento-2026",
    })
    assert second.status_code == 202
    second_client.headers.update({
    })

    campaign_id = owner_campaign["id"]
    assert second_client.get(f"/api/v1/campaigns/{campaign_id}/map").status_code == 404
    assert second_client.post(
        f"/api/v1/campaigns/{campaign_id}/move",
        json={"target_q": 1, "target_r": 0},
    ).status_code == 404
    assert second_client.post(
        f"/api/v1/campaigns/{campaign_id}/inventory/use",
        json={"item_id": "agua_potavel"},
    ).status_code == 404
    assert second_client.post(f"/api/v1/campaigns/{campaign_id}/rest").status_code == 404

    # O estado original continua intacto após todas as tentativas indevidas.
    original = client.get(f"/api/v1/campaigns/{campaign_id}").json()
    assert original["character"]["position_q"] == 0
    assert original["character"]["position_r"] == 0
    assert original["character"]["inventory"] == [
        "kit_atendimento_basico", "agua_potavel", "racao"
    ]
    assert original["world_time_minutes"] == 0


def test_all_campaign_mutations_require_authentication():
    """Rotas de mutação não aceitam chamadas anônimas."""
    campaign = create_campaign("Campanha protegida")
    anonymous = TestClient(app)
    campaign_id = campaign["id"]

    assert anonymous.post(
        f"/api/v1/campaigns/{campaign_id}/character",
        json={"name": "Intruso", "origin": "mecanico"},
    ).status_code == 401
    assert anonymous.post(
        f"/api/v1/campaigns/{campaign_id}/move",
        json={"target_q": 1, "target_r": 0},
    ).status_code == 401
    assert anonymous.post(
        f"/api/v1/campaigns/{campaign_id}/inventory/use",
        json={"item_id": "agua_potavel"},
    ).status_code == 401
    assert anonymous.post(f"/api/v1/campaigns/{campaign_id}/rest").status_code == 401



def test_auth_uses_http_only_session_cookie_and_logout_revokes_browser_session():
    """A sessão não é devolvida no JSON e o logout limpa o cookie HttpOnly."""
    account_client = TestClient(app)
    response = account_client.post("/api/v1/auth/register", json={
        "email": "cookie-session@example.com",
        "display_name": "Cookie Session",
        "password": "Senha-cookie-segura-2026",
    })
    assert response.status_code == 202
    assert "access_token" not in response.json()
    assert response.cookies.get("amazonia_session")
    assert response.cookies.get("amazonia_csrf")
    assert "HttpOnly" in response.headers.get("set-cookie", "")
    assert account_client.get("/api/v1/auth/me").status_code == 200
    browser_me = account_client.get("/api/v1/auth/me", headers={"Origin": "http://localhost:5173"})
    assert browser_me.status_code == 200  # GET não exige cabeçalho CSRF.

    # Mesmo que um cookie tenha sido copiado antes do logout, a versão da sessão o invalida.
    stolen_session = TestClient(app)
    stolen_session.cookies.set("amazonia_session", account_client.cookies.get("amazonia_session"))
    stolen_session.cookies.set("amazonia_csrf", account_client.cookies.get("amazonia_csrf"))
    logout = account_client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert account_client.get("/api/v1/auth/me").status_code == 401
    assert stolen_session.get("/api/v1/auth/me").status_code == 401


def test_browser_mutations_require_allowed_origin_and_csrf_token():
    """Rejeita origem externa e requisição de navegador sem token CSRF."""
    account_client = TestClient(app)
    registered = account_client.post("/api/v1/auth/register", json={
        "email": "csrf-session@example.com",
        "display_name": "CSRF Session",
        "password": "Senha-csrf-segura-2026",
    })
    assert registered.status_code == 202
    campaign = account_client.post(
        "/api/v1/campaigns",
        json={"name": "Campanha CSRF"},
        headers={"Origin": "https://evil.example"},
    )
    assert campaign.status_code == 403

    csrf_missing = account_client.post(
        "/api/v1/campaigns",
        json={"name": "Campanha sem CSRF"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert csrf_missing.status_code == 403

    csrf = account_client.cookies.get("amazonia_csrf")
    allowed = account_client.post(
        "/api/v1/campaigns",
        json={"name": "Campanha com CSRF"},
        headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
    )
    assert allowed.status_code == 201



def test_login_is_rate_limited_after_five_failed_attempts():
    """Limita tentativas inválidas por e-mail mesmo entre clientes distintos."""
    limited_client = TestClient(app)
    payload = {"email": "bruteforce@example.com", "password": "senha-errada"}
    for _ in range(5):
        response = limited_client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401
    blocked = limited_client.post("/api/v1/auth/login", json=payload)
    assert blocked.status_code == 429



def test_csrf_bootstrap_endpoint_supports_cross_origin_frontend():
    """O Web obtém o token CSRF pelo endpoint da API sem ler cookie de outro host."""
    browser = TestClient(app)
    response = browser.get("/api/v1/auth/csrf", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    assert token
    assert browser.cookies.get("amazonia_csrf") == token
    blocked = browser.post("/api/v1/campaigns", json={"name": "Sem sessão"}, headers={
        "Origin": "http://localhost:5173",
        "X-CSRF-Token": token,
    })
    assert blocked.status_code == 401  # CSRF válido, mas sem sessão autenticada.


def test_email_verification_is_required_and_owner_is_provisioned_only_after_verification(monkeypatch):
    """A conta só recebe sessão após confirmação; owner depende de e-mail confirmado."""
    monkeypatch.setenv("AMAZONIA_REQUIRE_EMAIL_VERIFICATION", "true")
    monkeypatch.setenv("AMAZONIA_OWNER_EMAIL", "owner-amazonia@example.com")
    sent = []
    monkeypatch.setattr(main_module, "send_account_email", lambda recipient, subject, body: sent.append(body))
    browser = TestClient(app)
    registration = browser.post("/api/v1/auth/register", json={
        "email": "owner-amazonia@example.com",
        "display_name": "Owner",
        "password": "Senha-segura-owner-2026",
    })
    assert registration.status_code == 202
    assert browser.get("/api/v1/auth/me").status_code == 401
    denied_login = browser.post("/api/v1/auth/login", json={
        "email": "owner-amazonia@example.com",
        "password": "Senha-segura-owner-2026",
    })
    assert denied_login.status_code == 401
    token = re.search(r"\?verify=([A-Za-z0-9_-]+)", sent[0]).group(1)
    verified = browser.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200
    assert browser.get("/api/v1/auth/me").status_code == 200
    with TestingSessionLocal() as session:
        owner = session.query(User).filter(User.email == "owner-amazonia@example.com").one()
        assert owner.role == "owner"
        assert owner.email_verified_at is not None
    assert browser.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400



def test_password_reset_token_is_single_use_and_revokes_existing_sessions(monkeypatch):
    """Recuperação troca a senha, consome o token e revoga cookies já emitidos."""
    monkeypatch.setenv("AMAZONIA_REQUIRE_EMAIL_VERIFICATION", "false")
    sent = []
    monkeypatch.setattr(main_module, "send_account_email", lambda recipient, subject, body: sent.append(body))
    browser = TestClient(app)
    registration = browser.post("/api/v1/auth/register", json={
        "email": "reset-amazonia@example.com",
        "display_name": "Reset",
        "password": "Senha-antiga-segura-2026",
    })
    assert registration.status_code == 202
    with TestingSessionLocal() as session:
        user = session.query(User).filter(User.email == "reset-amazonia@example.com").one()
        user.email_verified_at = datetime.now(timezone.utc)
        session.commit()
    requested = browser.post("/api/v1/auth/forgot-password", json={"email": "reset-amazonia@example.com"})
    assert requested.status_code == 202
    token = re.search(r"\?reset=([A-Za-z0-9_-]+)", sent[0]).group(1)
    reset = TestClient(app).post("/api/v1/auth/reset-password", json={
        "token": token,
        "password": "Senha-nova-segura-2026",
    })
    assert reset.status_code == 200
    assert browser.get("/api/v1/auth/me").status_code == 401
    new_login = TestClient(app).post("/api/v1/auth/login", json={
        "email": "reset-amazonia@example.com",
        "password": "Senha-nova-segura-2026",
    })
    assert new_login.status_code == 200
    reused = TestClient(app).post("/api/v1/auth/reset-password", json={
        "token": token,
        "password": "Outra-senha-segura-2026",
    })
    assert reused.status_code == 400


def test_character_appearance_is_validated_and_persisted():
    """Aceita cosméticos do catálogo e rejeita valores arbitrários."""
    campaign = create_campaign("Aparência personalizada")
    payload = {
        "name": "Joana",
        "origin": "mecanico",
        "appearance": {
            "hair_style": "trancas",
            "hair_color": "castanho",
            "eye_color": "verde",
            "skin_tone": "escuro",
            "tattoo_style": "geometrica",
            "tattoo_placement": "antebraco",
            "tattoo_scale": "media",
            "shirt_model": "jaqueta",
            "shirt_color": "bege",
            "pants_model": "tatico",
            "pants_color": "preta",
        },
    }
    created = client.post(f"/api/v1/campaigns/{campaign['id']}/character", json=payload)
    assert created.status_code == 201
    assert created.json()["appearance"] == payload["appearance"]
    persisted = client.get(f"/api/v1/campaigns/{campaign['id']}")
    assert persisted.json()["character"]["appearance"] == payload["appearance"]


def test_character_rejects_appearance_outside_catalog():
    """A API impede cosméticos não permitidos pelo catálogo do jogo."""
    campaign = create_campaign("Cosmético inválido")
    response = client.post(f"/api/v1/campaigns/{campaign['id']}/character", json={
        "name": "João",
        "origin": "bombeiro",
        "appearance": {"hair_style": "qualquer-coisa"},
    })
    assert response.status_code == 422
