"""Regras geográficas determinísticas e POIs públicos do protótipo."""
from __future__ import annotations

from math import cos, radians, sin, sqrt
from typing import Any

ORIGIN_LATITUDE = -23.5505
ORIGIN_LONGITUDE = -46.6333
HEX_RADIUS_METERS = 500.0
MOVE_COST_MINUTES = 10
VISIBLE_CELL_RADIUS = 2
MAX_CELL_COORDINATE = 50

# Coordenadas municipais publicadas no Anexo I da Portaria SIURB 1/2019.
# Os pontos são referências cartográficas; não afirmam disponibilidade de recursos no jogo.
POI_CATALOG: tuple[dict[str, object], ...] = (
    {
        "id": "praca_se",
        "name": "Praça da Sé",
        "category": "praça",
        "latitude": -23.55037,
        "longitude": -46.63395,
        "description": "Praça no Centro Histórico.",
    },
    {
        "id": "pateo_do_colegio",
        "name": "Pátio do Colégio",
        "category": "ponto_turistico",
        "latitude": -23.54807,
        "longitude": -46.63295,
        "description": "Marco histórico no Centro.",
    },
    {
        "id": "mercado_municipal",
        "name": "Mercado Municipal",
        "category": "ponto_turistico",
        "latitude": -23.54176,
        "longitude": -46.62939,
        "description": "Referência urbana na região central.",
    },
    {
        "id": "parque_da_luz",
        "name": "Parque da Luz",
        "category": "parque",
        "latitude": -23.53311,
        "longitude": -46.63558,
        "description": "Área verde na região da Luz.",
    },
    {
        "id": "parque_dom_pedro_ii",
        "name": "Parque Dom Pedro II",
        "category": "parque",
        "latitude": -23.545424,
        "longitude": -46.627899,
        "description": "Área pública no Centro.",
    },
    {
        "id": "masp",
        "name": "MASP",
        "category": "ponto_turistico",
        "latitude": -23.56132,
        "longitude": -46.65586,
        "description": "Ponto de referência na Avenida Paulista.",
    },
    {
        "id": "centro_cultural_sao_paulo",
        "name": "Centro Cultural São Paulo",
        "category": "centro_cultural",
        "latitude": -23.57072,
        "longitude": -46.64025,
        "description": "Equipamento cultural na região da Liberdade.",
    },
    {
        "id": "parque_da_aclimacao",
        "name": "Parque da Aclimação",
        "category": "parque",
        "latitude": -23.57256,
        "longitude": -46.62885,
        "description": "Área verde urbana.",
    },
    {
        "id": "parque_da_independencia",
        "name": "Parque da Independência",
        "category": "parque",
        "latitude": -23.58503,
        "longitude": -46.60973,
        "description": "Parque na região do Ipiranga.",
    },
)


def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Calcula distância em uma grade hexagonal axial."""
    delta_q = q2 - q1
    delta_r = r2 - r1
    return max(abs(delta_q), abs(delta_r), abs(delta_q + delta_r))


def cell_center(q: int, r: int) -> tuple[float, float]:
    """Converte coordenadas axiais em latitude/longitude aproximadas."""
    east_meters = HEX_RADIUS_METERS * sqrt(3) * (q + r / 2)
    north_meters = HEX_RADIUS_METERS * 1.5 * r
    latitude = ORIGIN_LATITUDE + north_meters / 111_320
    longitude = ORIGIN_LONGITUDE + east_meters / (
        111_320 * cos(radians(ORIGIN_LATITUDE))
    )
    return latitude, longitude


def latlon_to_cell(latitude: float, longitude: float) -> tuple[int, int]:
    """Encontra a célula axial mais próxima de uma coordenada geográfica."""
    north_meters = (latitude - ORIGIN_LATITUDE) * 111_320
    east_meters = (longitude - ORIGIN_LONGITUDE) * 111_320 * cos(radians(ORIGIN_LATITUDE))
    r_float = north_meters / (1.5 * HEX_RADIUS_METERS)
    q_float = east_meters / (sqrt(3) * HEX_RADIUS_METERS) - r_float / 2

    x_float = q_float
    z_float = r_float
    y_float = -x_float - z_float
    x_round, y_round, z_round = round(x_float), round(y_float), round(z_float)
    x_error = abs(x_round - x_float)
    y_error = abs(y_round - y_float)
    z_error = abs(z_round - z_float)

    if x_error > y_error and x_error > z_error:
        x_round = -y_round - z_round
    elif y_error > z_error:
        y_round = -x_round - z_round
    else:
        z_round = -x_round - y_round
    return int(x_round), int(z_round)


def cell_key(q: int, r: int) -> str:
    """Gera chave estável para registrar uma célula descoberta."""
    return f"{q}:{r}"


def build_map_data(campaign: Any, character: Any) -> dict[str, Any]:
    """Monta células visíveis e POIs apenas das células já descobertas."""
    current_q = character.position_q
    current_r = character.position_r
    discovered = set(character.discovered_cells or [])
    cells: list[dict[str, Any]] = []

    for q in range(current_q - VISIBLE_CELL_RADIUS, current_q + VISIBLE_CELL_RADIUS + 1):
        for r in range(current_r - VISIBLE_CELL_RADIUS, current_r + VISIBLE_CELL_RADIUS + 1):
            distance = hex_distance(current_q, current_r, q, r)
            if distance > VISIBLE_CELL_RADIUS:
                continue
            latitude, longitude = cell_center(q, r)
            cells.append({
                "q": q,
                "r": r,
                "latitude": latitude,
                "longitude": longitude,
                "radius_meters": HEX_RADIUS_METERS,
                "discovered": cell_key(q, r) in discovered,
                "current": q == current_q and r == current_r,
                "adjacent": distance == 1,
            })

    visible_discovered = {
        cell_key(cell["q"], cell["r"])
        for cell in cells
        if cell["discovered"]
    }
    points_of_interest: list[dict[str, object]] = []
    for poi in POI_CATALOG:
        poi_q, poi_r = latlon_to_cell(float(poi["latitude"]), float(poi["longitude"]))
        if cell_key(poi_q, poi_r) not in visible_discovered:
            continue
        points_of_interest.append({
            **poi,
            "cell_q": poi_q,
            "cell_r": poi_r,
        })

    return {
        "campaign_id": campaign.id,
        "world_time_minutes": campaign.world_time_minutes,
        "player_position": {
            "q": current_q,
            "r": current_r,
            "latitude": cell_center(current_q, current_r)[0],
            "longitude": cell_center(current_q, current_r)[1],
        },
        "hex_radius_meters": HEX_RADIUS_METERS,
        "cells": cells,
        "points_of_interest": points_of_interest,
    }
