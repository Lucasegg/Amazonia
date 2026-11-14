import pytest

from scripts.download_osm_pois import (
    build_query,
    classify_tags,
    element_to_feature,
    to_feature_collection,
)


def test_build_query_is_limited_to_sao_paulo_prototype_area():
    query = build_query()
    assert "[out:json][timeout:60]" in query
    assert "around:5000,-23.550500,-46.633300" in query
    assert '["amenity"~"' in query
    assert "out center tags;" in query


def test_build_query_rejects_unreasonable_radius():
    with pytest.raises(ValueError, match="Raio"):
        build_query(radius_meters=100_000)


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ({"amenity": "clinic"}, "healthcare"),
        ({"amenity": "police"}, "police"),
        ({"amenity": "fire_station"}, "fire_station"),
        ({"amenity": "drinking_water"}, "water"),
        ({"shop": "supermarket"}, "market"),
        ({"shop": "bakery"}, "food"),
        ({"railway": "station"}, "transport"),
        ({"leisure": "park"}, "park"),
        ({"tourism": "hostel"}, "shelter"),
    ],
)
def test_classify_tags_maps_supported_osm_categories(tags, expected):
    assert classify_tags(tags) == expected


def test_element_to_feature_creates_attributed_osm_point():
    element = {
        "type": "node",
        "id": 12345,
        "lat": -23.5505,
        "lon": -46.6333,
        "tags": {"name": "Unidade de Saúde", "amenity": "clinic", "wheelchair": "yes"},
    }
    feature = element_to_feature(element)
    assert feature is not None
    assert feature["geometry"]["coordinates"] == [-46.6333, -23.5505]
    assert feature["properties"]["category"] == "healthcare"
    assert feature["properties"]["source_ref"] == "osm:node:12345"
    assert feature["properties"]["source_license"] == "ODbL-1.0"
    assert feature["properties"]["source_url"] == "https://www.openstreetmap.org/node/12345"


def test_way_uses_overpass_center_for_point_geometry():
    element = {
        "type": "way",
        "id": 987,
        "center": {"lat": -23.55, "lon": -46.63},
        "tags": {"name": "Mercado", "shop": "supermarket"},
    }
    feature = element_to_feature(element)
    assert feature is not None
    assert feature["geometry"]["coordinates"] == [-46.63, -23.55]
    assert feature["properties"]["source_ref"] == "osm:way:987"


def test_unnamed_or_uncategorized_elements_are_skipped():
    assert element_to_feature({
        "type": "node", "id": 1, "lat": -23.55, "lon": -46.63,
        "tags": {"amenity": "clinic"},
    }) is None
    assert element_to_feature({
        "type": "node", "id": 2, "lat": -23.55, "lon": -46.63,
        "tags": {"name": "Local sem categoria"},
    }) is None


def test_feature_collection_is_deduplicated_and_has_odbl_attribution():
    payload = {
        "osm3s": {"timestamp_osm_base": "2026-11-14T00:00:00Z"},
        "elements": [
            {
                "type": "node", "id": 10, "lat": -23.55, "lon": -46.63,
                "tags": {"name": "Clínica", "amenity": "clinic"},
            },
            {
                "type": "node", "id": 10, "lat": -23.55, "lon": -46.63,
                "tags": {"name": "Clínica", "amenity": "clinic"},
            },
        ],
    }
    collection = to_feature_collection(payload)
    assert collection["license"] == "ODbL-1.0"
    assert collection["attribution"] == "© OpenStreetMap contributors"
    assert collection["osm_base_timestamp"] == "2026-11-14T00:00:00Z"
    assert len(collection["features"]) == 1


def test_feature_collection_rejects_partial_overpass_response():
    with pytest.raises(RuntimeError, match="resposta parcial"):
        to_feature_collection({"remark": "runtime error: Query timed out", "elements": []})
