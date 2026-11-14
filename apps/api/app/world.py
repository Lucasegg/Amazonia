"""Catálogo geográfico e funções de exploração do protótipo."""
from __future__ import annotations

from math import asin, ceil, cos, radians, sin, sqrt

SPAWN_LOCATION_ID = "praca_se"
SPAWN_POSITION = {
    "location_id": SPAWN_LOCATION_ID,
    "latitude": -23.55037,
    "longitude": -46.63395,
}
SEARCH_RADIUS_KM = 2.0
SEARCH_ACTION_MINUTES = 15
WALKING_SPEED_KMH = 4.0

# Coordenadas de referência obtidas de bases públicas municipais de São Paulo.
# O ponto inicial é provisório e pode ser alterado sem mudar as regras do domínio.
LOCATIONS: dict[str, dict[str, object]] = {
    "praca_se": {
        "id": "praca_se", "name": "Praça da Sé", "category": "praça",
        "latitude": -23.55037, "longitude": -46.63395,
        "description": "Ponto inicial de referência do protótipo.",
    },
    "pateo_do_colegio": {
        "id": "pateo_do_colegio", "name": "Pátio do Colégio", "category": "cultural",
        "latitude": -23.54807, "longitude": -46.63295,
        "description": "Marco cultural do Centro Histórico.",
    },
    "mercado_municipal": {
        "id": "mercado_municipal", "name": "Mercado Municipal", "category": "mercado",
        "latitude": -23.54176, "longitude": -46.62939,
        "description": "Ponto de referência comercial e de abastecimento.",
    },
    "parque_da_luz": {
        "id": "parque_da_luz", "name": "Parque da Luz", "category": "parque",
        "latitude": -23.53311, "longitude": -46.63558,
        "description": "Área verde na região central.",
    },
    "parque_dom_pedro_ii": {
        "id": "parque_dom_pedro_ii", "name": "Parque Dom Pedro II", "category": "parque",
        "latitude": -23.545424, "longitude": -46.627899,
        "description": "Área pública próxima ao Centro Histórico.",
    },
    "masp": {
        "id": "masp", "name": "MASP", "category": "cultural",
        "latitude": -23.56132, "longitude": -46.65586,
        "description": "Ponto cultural da Avenida Paulista.",
    },
    "centro_cultural_sao_paulo": {
        "id": "centro_cultural_sao_paulo", "name": "Centro Cultural São Paulo", "category": "cultural",
        "latitude": -23.57072, "longitude": -46.64025,
        "description": "Equipamento cultural próximo à região central.",
    },
    "parque_da_aclimacao": {
        "id": "parque_da_aclimacao", "name": "Parque da Aclimação", "category": "parque",
        "latitude": -23.57256, "longitude": -46.62885,
        "description": "Área verde urbana.",
    },
    "parque_da_independencia": {
        "id": "parque_da_independencia", "name": "Parque da Independência", "category": "parque",
        "latitude": -23.58503, "longitude": -46.60973,
        "description": "Área pública do bairro do Ipiranga.",
    },
}


def distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    """Calcula distância geodésica aproximada pela fórmula de Haversine."""
    earth_radius_km = 6371.0088
    lat_delta = radians(latitude_b - latitude_a)
    lon_delta = radians(longitude_b - longitude_a)
    a = sin(lat_delta / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(lon_delta / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def travel_minutes(distance: float) -> int:
    """Estima deslocamento a pé a 4 km/h, arredondando para cima."""
    return max(1, ceil(distance / WALKING_SPEED_KMH * 60))


def map_payload(campaign_id: str, world_time_minutes: int, character) -> dict[str, object]:
    """Retorna somente locais já conhecidos pelo personagem."""
    latitude = float(character.position["latitude"])
    longitude = float(character.position["longitude"])
    known = []
    for location_id in character.discovered_locations:
        location = LOCATIONS.get(location_id)
        if location is None:
            continue
        item = dict(location)
        item["distance_km"] = round(
            distance_km(latitude, longitude, float(location["latitude"]), float(location["longitude"])),
            2,
        )
        known.append(item)
    return {
        "campaign_id": campaign_id,
        "world_time_minutes": world_time_minutes,
        "current_position": dict(character.position),
        "known_locations": known,
    }
