"""Regras geográficas determinísticas para o protótipo de exploração."""
from __future__ import annotations

from math import cos, radians, sqrt
from typing import Any, Iterable

ORIGIN_LATITUDE = -23.5505
ORIGIN_LONGITUDE = -46.6333
HEX_RADIUS_METERS = 500.0
MOVE_COST_MINUTES = 10
VISIBLE_CELL_RADIUS = 2
MAX_CELL_COORDINATE = 50


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
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Latitude ou longitude fora do intervalo válido.")

    east_meters = (longitude - ORIGIN_LONGITUDE) * 111_320 * cos(radians(ORIGIN_LATITUDE))
    north_meters = (latitude - ORIGIN_LATITUDE) * 111_320
    q_fraction = (sqrt(3) / 3 * east_meters - north_meters / 3) / HEX_RADIUS_METERS
    r_fraction = (2 * north_meters / 3) / HEX_RADIUS_METERS
    s_fraction = -q_fraction - r_fraction

    q_round = round(q_fraction)
    r_round = round(r_fraction)
    s_round = round(s_fraction)
    q_error = abs(q_round - q_fraction)
    r_error = abs(r_round - r_fraction)
    s_error = abs(s_round - s_fraction)

    if q_error > r_error and q_error > s_error:
        q_round = -r_round - s_round
    elif r_error > s_error:
        r_round = -q_round - s_round

    return int(q_round), int(r_round)


def cell_key(q: int, r: int) -> str:
    """Gera chave estável para registrar uma célula descoberta."""
    return f"{q}:{r}"


def build_map_data(
    campaign: Any,
    character: Any,
    points_of_interest: Iterable[Any] = (),
) -> dict[str, Any]:
    """Monta células visíveis e revela POIs apenas em células descobertas."""
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

    visible_pois = [
        {
            "id": poi.id,
            "name": poi.name,
            "category": poi.category,
            "latitude": poi.latitude,
            "longitude": poi.longitude,
            "cell_q": poi.cell_q,
            "cell_r": poi.cell_r,
            "source": poi.source,
            "source_license": poi.source_license,
        }
        for poi in points_of_interest
        if cell_key(poi.cell_q, poi.cell_r) in discovered
    ]

    current_latitude, current_longitude = cell_center(current_q, current_r)
    return {
        "campaign_id": campaign.id,
        "world_time_minutes": campaign.world_time_minutes,
        "player_position": {
            "q": current_q,
            "r": current_r,
            "latitude": current_latitude,
            "longitude": current_longitude,
        },
        "hex_radius_meters": HEX_RADIUS_METERS,
        "cells": cells,
        "points_of_interest": visible_pois,
    }
