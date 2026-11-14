"""Regras geográficas determinísticas para o protótipo de exploração."""
from __future__ import annotations

from math import cos, radians, sin, sqrt
from typing import Any

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


def cell_key(q: int, r: int) -> str:
    """Gera chave estável para registrar uma célula descoberta."""
    return f"{q}:{r}"


def build_map_data(campaign: Any, character: Any) -> dict[str, Any]:
    """Monta células visíveis sem revelar dados de áreas ainda desconhecidas."""
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
    }
