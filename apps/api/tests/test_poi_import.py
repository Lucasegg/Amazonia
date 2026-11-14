import pytest

from app.domain.world import cell_center, latlon_to_cell
from scripts.import_pois_geojson import parse_feature


def test_cell_conversion_round_trips_for_prototype_cells():
    for q, r in [(0, 0), (1, 0), (0, 1), (-2, 1), (3, -2)]:
        latitude, longitude = cell_center(q, r)
        assert latlon_to_cell(latitude, longitude) == (q, r)


def test_parse_feature_assigns_source_and_hex_cell():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Unidade de Saúde Exemplo",
            "category": "healthcare",
            "source_ref": "osm:node:123456",
            "tags": {"amenity": "clinic", "wheelchair": "yes"},
        },
    }
    result = parse_feature(feature)
    assert result is not None
    assert result["source_ref"] == "osm:node:123456"
    assert result["cell_q"] == 0
    assert result["cell_r"] == 0
    assert result["source_license"] == "ODbL-1.0"
    assert result["tags"]["amenity"] == "clinic"


def test_parse_feature_skips_unnamed_places():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {"category": "food", "source_ref": "osm:node:9"},
    }
    assert parse_feature(feature) is None


def test_parse_feature_rejects_unknown_categories():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {"name": "Local", "category": "not-a-category", "source_ref": "x:1"},
    }
    with pytest.raises(ValueError):
        parse_feature(feature)
