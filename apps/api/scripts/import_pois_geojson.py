"""Importa POIs de um GeoJSON público para o catálogo do Amazonia.

O script não faz scraping nem busca dados na inicialização da API. O arquivo
GeoJSON deve ser obtido de uma fonte pública licenciada e conter atribuição.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

from app.database import SessionLocal
from app.domain.world import MAX_CELL_COORDINATE, latlon_to_cell
from app.models import PointOfInterest

ALLOWED_CATEGORIES = {
    "healthcare", "police", "fire_station", "pharmacy", "food", "fuel",
    "shelter", "school", "transport", "market", "other",
}


def parse_feature(feature: dict) -> dict | None:
    """Valida e normaliza uma Feature GeoJSON Point; ignora dados sem nome."""
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise ValueError("Cada item precisa ser uma GeoJSON Feature.")
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Point":
        raise ValueError("POI precisa usar geometria Point.")

    coordinates = geometry.get("coordinates") or []
    if not isinstance(coordinates, list) or len(coordinates) < 2:
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
    osm_type = str(properties.get("osm_type") or "").strip()
    osm_id = str(properties.get("osm_id") or "").strip()
    if not source_ref and osm_type and osm_id:
        source_ref = f"osm:{osm_type}:{osm_id}"
    if not source_ref:
        raise ValueError("POI precisa de source_ref estável para evitar duplicação.")
    if len(source_ref) > 120:
        raise ValueError("source_ref excede o limite de 120 caracteres.")

    if abs(q) > MAX_CELL_COORDINATE or abs(r) > MAX_CELL_COORDINATE:
        return None

    source = str(properties.get("source") or "").strip()
    if not source and source_ref.startswith("osm:"):
        source = "OpenStreetMap"
    if not source:
        raise ValueError("POI precisa identificar a fonte dos dados.")
    if len(source) > 40:
        raise ValueError("source excede o limite de 40 caracteres.")
    if source == "OpenStreetMap" and not source_ref.startswith("osm:"):
        raise ValueError("Registros OpenStreetMap precisam de source_ref osm:type:id.")

    source_license = str(properties.get("source_license") or "").strip()
    if not source_license and source == "OpenStreetMap":
        source_license = "ODbL-1.0"
    if not source_license:
        raise ValueError(
            f"POI da fonte {source!r} precisa declarar source_license explicitamente."
        )
    if source == "OpenStreetMap" and source_license != "ODbL-1.0":
        raise ValueError("Dados OpenStreetMap precisam preservar a licença ODbL-1.0.")
    if len(source_license) > 40:
        raise ValueError("source_license excede o limite de 40 caracteres.")

    source_url = str(properties.get("source_url") or "").strip()
    if not source_url and source == "OpenStreetMap":
        parts = source_ref.split(":")
        if len(parts) == 3 and parts[0] == "osm":
            source_url = f"https://www.openstreetmap.org/{parts[1]}/{parts[2]}"
        else:
            source_url = "https://www.openstreetmap.org/"
    parsed_url = urlparse(source_url)
    if not parsed_url.scheme or not parsed_url.netloc or parsed_url.scheme not in {"http", "https"}:
        raise ValueError("POI precisa de source_url HTTP ou HTTPS válido.")
    if len(source_url) > 255:
        raise ValueError("source_url excede o limite de 255 caracteres.")

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
        "source": source,
        "source_license": source_license,
        "source_url": source_url,
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
