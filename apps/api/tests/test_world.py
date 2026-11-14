"""Testes unitários do catálogo geográfico e deslocamento."""
from app.world import (
    LOCATIONS,
    SEARCH_RADIUS_KM,
    SPAWN_POSITION,
    distance_km,
    travel_minutes,
)


def test_spawn_is_a_real_published_city_reference() -> None:
    """O spawn provisório coincide com a coordenada municipal da Praça da Sé."""
    place = LOCATIONS["praca_se"]
    assert SPAWN_POSITION["latitude"] == place["latitude"]
    assert SPAWN_POSITION["longitude"] == place["longitude"]


def test_distance_to_pateo_is_within_first_search_radius() -> None:
    """Pátio do Colégio fica dentro do raio inicial de busca."""
    spawn = LOCATIONS["praca_se"]
    target = LOCATIONS["pateo_do_colegio"]
    distance = distance_km(
        float(spawn["latitude"]),
        float(spawn["longitude"]),
        float(target["latitude"]),
        float(target["longitude"]),
    )
    assert 0 < distance < SEARCH_RADIUS_KM


def test_distance_from_point_to_itself_is_zero() -> None:
    """A distância de um ponto para ele mesmo é zero."""
    assert distance_km(-23.55, -46.63, -23.55, -46.63) == 0


def test_walking_time_rounds_up_to_whole_minutes() -> None:
    """A estimativa de caminhada nunca retorna zero para um deslocamento."""
    assert travel_minutes(0) == 1
    assert travel_minutes(1) == 15
    assert travel_minutes(1.01) == 16
