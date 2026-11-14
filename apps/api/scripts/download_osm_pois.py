"""Baixa uma única extração de POIs do Overpass e grava GeoJSON local.

Não é chamado pela API nem pelo jogo em tempo de execução. Executar manualmente
e com moderação; o servidor público é comunitário e não oferece SLA.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
USER_AGENT = "Amazonia-POI-Importer/1.0 (+https://github.com/Lucasegg/Amazonia)"

AMENITY_VALUES = (
    "hospital", "clinic", "doctors", "dentist", "police", "fire_station",
    "pharmacy", "restaurant", "cafe", "fast_food", "food_court", "fuel",
    "shelter", "school", "college", "university", "marketplace", "drinking_water",
)
SHOP_VALUES = ("supermarket", "convenience", "bakery", "butcher", "greengrocer", "marketplace")
RAILWAY_VALUES = ("station", "subway_entrance")
TOURISM_VALUES = ("hostel", "camp_site")


def build_query(
    center_lat: float = -23.5505,
    center_lon: float = -46.6333,
    radius_meters: int = 5000,
    timeout_seconds: int = 60,
) -> str:
    """Monta uma consulta única e limitada à área do protótipo."""
    if not -90 <= center_lat <= 90 or not -180 <= center_lon <= 180:
        raise ValueError("Coordenadas centrais inválidas.")
    if not 100 <= radius_meters <= 50_000:
        raise ValueError("Raio precisa estar entre 100 e 50.000 metros.")
    if not 10 <= timeout_seconds <= 180:
        raise ValueError("Timeout precisa estar entre 10 e 180 segundos.")

    amenity_pattern = "^(" + "|".join(AMENITY_VALUES) + ")$"
    shop_pattern = "^(" + "|".join(SHOP_VALUES) + ")$"
    railway_pattern = "^(" + "|".join(RAILWAY_VALUES) + ")$"
    tourism_pattern = "^(" + "|".join(TOURISM_VALUES) + ")$"
    area = f"(around:{radius_meters},{center_lat:.6f},{center_lon:.6f})"
    return f"""[out:json][timeout:{timeout_seconds}];
(
  nwr{area}["amenity"~"{amenity_pattern}"];
  nwr{area}["shop"~"{shop_pattern}"];
  nwr{area}["public_transport"="station"];
  nwr{area}["railway"~"{railway_pattern}"];
  nwr{area}["leisure"="park"];
  nwr{area}["tourism"~"{tourism_pattern}"];
);
out center tags;
"""


def classify_tags(tags: dict[str, str]) -> str | None:
    """Converte tags OSM em categorias controladas pelo catálogo do jogo."""
    amenity = tags.get("amenity", "")
    shop = tags.get("shop", "")
    railway = tags.get("railway", "")
    public_transport = tags.get("public_transport", "")
    leisure = tags.get("leisure", "")
    tourism = tags.get("tourism", "")

    if amenity in {"hospital", "clinic", "doctors", "dentist"}:
        return "healthcare"
    if amenity == "police":
        return "police"
    if amenity == "fire_station":
        return "fire_station"
    if amenity == "pharmacy":
        return "pharmacy"
    if amenity == "drinking_water":
        return "water"
    if amenity in {"restaurant", "cafe", "fast_food", "food_court"}:
        return "food"
    if amenity == "fuel":
        return "fuel"
    if amenity == "shelter" or tourism in {"hostel", "camp_site"}:
        return "shelter"
    if amenity in {"school", "college", "university"}:
        return "school"
    if amenity == "marketplace" or shop in {"supermarket", "convenience", "marketplace"}:
        return "market"
    if shop in {"bakery", "butcher", "greengrocer"}:
        return "food"
    if public_transport == "station" or railway in {"station", "subway_entrance"}:
        return "transport"
    if leisure == "park":
        return "park"
    return None


def element_to_feature(element: dict) -> dict | None:
    """Normaliza node/way/relation OSM para GeoJSON Point com atribuição."""
    element_type = element.get("type")
    element_id = element.get("id")
    if element_type not in {"node", "way", "relation"} or not isinstance(element_id, int):
        return None

    tags = element.get("tags") or {}
    if not isinstance(tags, dict):
        return None
    name = str(tags.get("name") or tags.get("name:pt") or "").strip()
    if not name:
        return None
    category = classify_tags({str(key): str(value) for key, value in tags.items()})
    if category is None:
        return None

    if element_type == "node":
        latitude, longitude = element.get("lat"), element.get("lon")
    else:
        center = element.get("center") or {}
        latitude, longitude = center.get("lat"), center.get("lon")
    if latitude is None or longitude is None:
        return None

    source_ref = f"osm:{element_type}:{element_id}"
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(longitude), float(latitude)],
        },
        "properties": {
            "name": name,
            "category": category,
            "source_ref": source_ref,
            "source": "OpenStreetMap",
            "source_license": "ODbL-1.0",
            "source_url": f"https://www.openstreetmap.org/{element_type}/{element_id}",
            "tags": {str(key): str(value) for key, value in tags.items()},
        },
    }


def to_feature_collection(payload: dict) -> dict:
    """Valida resposta Overpass e produz FeatureCollection determinística."""
    if not isinstance(payload, dict):
        raise ValueError("Resposta Overpass inválida.")
    if payload.get("remark"):
        raise RuntimeError(f"Overpass retornou resposta parcial: {payload['remark']}")
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise ValueError("Resposta Overpass não contém lista de elements.")

    features_by_ref: dict[str, dict] = {}
    for element in elements:
        if not isinstance(element, dict):
            continue
        feature = element_to_feature(element)
        if feature is not None:
            features_by_ref[feature["properties"]["source_ref"]] = feature

    timestamp = (payload.get("osm3s") or {}).get("timestamp_osm_base")
    return {
        "type": "FeatureCollection",
        "name": "Amazonia — pontos de interesse OpenStreetMap",
        "attribution": "© OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "osm_base_timestamp": timestamp,
        "features": [features_by_ref[key] for key in sorted(features_by_ref)],
    }


def fetch_overpass(endpoint: str, query: str, timeout_seconds: int) -> dict:
    """Executa uma requisição serial e identificada; não faz retry automático."""
    request = Request(
        endpoint,
        data=urlencode({"data": query}).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds + 15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera GeoJSON de POIs OSM para importação manual.")
    parser.add_argument("--output", required=True, type=Path, help="Arquivo GeoJSON de saída.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Instância Overpass.")
    parser.add_argument("--center-lat", type=float, default=-23.5505)
    parser.add_argument("--center-lon", type=float, default=-46.6333)
    parser.add_argument("--radius-meters", type=int, default=5000)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    try:
        query = build_query(
            args.center_lat,
            args.center_lon,
            args.radius_meters,
            args.timeout_seconds,
        )
        payload = fetch_overpass(args.endpoint, query, args.timeout_seconds)
        collection = to_feature_collection(payload)
    except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Falha ao obter POIs: {exc}. Não houve novas tentativas automáticas.\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(collection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"GeoJSON salvo: {args.output} | POIs nomeados: {len(collection['features'])} "
        f"| base OSM: {collection['osm_base_timestamp'] or 'não informada'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
