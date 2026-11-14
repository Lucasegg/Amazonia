"""Importa POIs de um GeoJSON público para o catálogo do Amazonia.

O script não faz scraping nem busca dados na inicialização da API. O arquivo
GeoJSON deve ser obtido de uma fonte pública licenciada e conter atribuição.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.database import SessionLocal
from app.domain.world import MAX_CELL_COORDINATE, latlon_to_cell
from app.models import PointOfInterest

ALLOWED_CATEGORIES = {
    "healthcare",
    "police",
    "fire_station",
    "pharmacy",
    "food",
    "fuel",
    "shelter",
    "school",
    "transport",
    "market",
    "other",
}


def parse_feature(feature: dict) -> dict | None:
    """Valida e normaliza uma Feature GeoJSON Point; ignora dados sem nome."""
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Point":
        raise ValueError("POI precisa usar geometria Point.")

    coordinates = geometry.get("coordinates") or []
    if len(coordinates) < 2:
        raise ValueError("POI precisa informar longitude e latitude.")
    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    q, r = latlon_to_cell(latitude, longitude)

    name = str(properties.get("name") or "").strip()
    if not name:
        return None

    category = str(properties.get("category") or "other").strip().lower()
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Categoria não permitida: {category}")

    source_ref = str(properties.get("source_ref") or "").strip()
    if not source_ref and properties.get("osm_type") and properties.get("osm_id"):
        source_ref = f"osm:{properties['osm_type']}:{properties['osm_id']}"
    if not source_ref:
        raise ValueError("POI precisa de source_ref estável para evitar duplicação.")

    if abs(q) > MAX_CELL_COORDINATE or abs(r) > MAX_CELL_COORDINATE:
        return None

    raw_tags = properties.get("tags") or {}
    tags = {str(key): str(value) for key, value in raw_tags.items()} if isinstance(raw_tags, dict) else {}

    return {
        "id": str(uuid5(NAMESPACE_URL, source_ref)),
        "source_ref": source_ref,
        "name": name[:120],
        "category": category,
        "latitude": latitude,
        "longitude": longitude,
        "cell_q": q,
        "cell_r": r,
        "tags": tags,
        "source": str(properties.get("source") or "OpenStreetMap")[:40],
        "source_license": str(properties.get("source_license") or "ODbL-1.0")[:40],
        "source_url": str(properties.get("source_url") or "https://www.openstreetmap.org/")[:255],
    }


def import_features(features: list[dict], session) -> tuple[int, int]:
    """Faz upsert por source_ref e retorna (importados, ignorados)."""
    imported = 0
    skipped = 0
    for feature in features:
        normalized = parse_feature(feature)
        if normalized is None:
            skipped += 1
            continue
        session.merge(PointOfInterest(**normalized))
        imported += 1
    session.commit()
    return imported, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa pontos de interesse a partir de GeoJSON.")
    parser.add_argument("--input", required=True, type=Path, help="Caminho para um FeatureCollection GeoJSON.")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        parser.error("O arquivo precisa ser um GeoJSON FeatureCollection.")

    session = SessionLocal()
    try:
        imported, skipped = import_features(payload["features"], session)
    finally:
        session.close()

    print(f"POIs importados/atualizados: {imported}; ignorados: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
