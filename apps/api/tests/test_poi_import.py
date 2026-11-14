import pytest

from app.domain.world import cell_center, latlon_to_cell
from scripts.import_pois_geojson import parse_feature


def test_cell_conversion_round_trips_for_prototype_cells():
    for q, r in [(0, 0), (1, 0), (0, 1), (-2, 1), (3, -2)]:
        latitude, longitude = cell_center(q, r)
        assert latlon_to_cell(latitude, longitude) == (q, r)


def test_parse_feature_assigns_osm_source_and_hex_cell():
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
    assert result["source"] == "OpenStreetMap"
    assert result["source_license"] == "ODbL-1.0"
    assert result["source_url"] == "https://www.openstreetmap.org/node/123456"
    assert result["tags"]["amenity"] == "clinic"


@pytest.mark.parametrize("category", ["water", "park"])
def test_parse_feature_accepts_new_world_categories(category):
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Ponto de referência",
            "category": category,
            "source_ref": "osm:node:555",
        },
    }
    result = parse_feature(feature)
    assert result is not None
    assert result["category"] == category


def test_parse_feature_preserves_geosampa_cc_by_sa_license():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Unidade de Saúde Municipal",
            "category": "healthcare",
            "source_ref": "geosampa:ubs:123",
            "source": "GeoSampa",
            "source_license": "CC-BY-SA-4.0",
            "source_url": "https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/bc44ee6c-e973-4670-b912-9ac8d64b9f56",
        },
    }
    result = parse_feature(feature)
    assert result is not None
    assert result["source"] == "GeoSampa"
    assert result["source_license"] == "CC-BY-SA-4.0"
    assert result["source_url"].startswith("https://metadados.geosampa")


def test_parse_feature_rejects_non_osm_source_without_license():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Unidade de Saúde Municipal",
            "category": "healthcare",
            "source_ref": "geosampa:ubs:123",
            "source": "GeoSampa",
            "source_url": "https://metadados.geosampa.prefeitura.sp.gov.br/",
        },
    }
    with pytest.raises(ValueError, match="source_license"):
        parse_feature(feature)


def test_parse_feature_rejects_non_http_source_url():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Unidade de Saúde Municipal",
            "category": "healthcare",
            "source_ref": "geosampa:ubs:124",
            "source": "GeoSampa",
            "source_license": "CC-BY-SA-4.0",
            "source_url": "file:///tmp/ubs.geojson",
        },
    }
    with pytest.raises(ValueError, match="source_url"):
        parse_feature(feature)


def test_parse_feature_rejects_openstreetmap_with_non_osm_reference():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Local",
            "category": "other",
            "source_ref": "other:123",
            "source": "OpenStreetMap",
            "source_license": "ODbL-1.0",
            "source_url": "https://www.openstreetmap.org/",
        },
    }
    with pytest.raises(ValueError, match="osm:type:id"):
        parse_feature(feature)


def test_parse_feature_rejects_malformed_osm_reference():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Local",
            "category": "other",
            "source_ref": "osm:invalid:abc",
        },
    }
    with pytest.raises(ValueError, match="osm:node"):
        parse_feature(feature)


def test_parse_feature_rejects_osm_reference_with_other_source():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Local",
            "category": "other",
            "source_ref": "osm:node:999",
            "source": "GeoSampa",
            "source_license": "CC-BY-SA-4.0",
            "source_url": "https://metadados.geosampa.prefeitura.sp.gov.br/",
        },
    }
    with pytest.raises(ValueError, match="não pode ser atribuído"):
        parse_feature(feature)


def test_parse_feature_rejects_openstreetmap_with_wrong_license():
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-46.6333, -23.5505]},
        "properties": {
            "name": "Local",
            "category": "other",
            "source_ref": "osm:node:999",
            "source": "OpenStreetMap",
            "source_license": "CC0",
            "source_url": "https://www.openstreetmap.org/node/999",
        },
    }
    with pytest.raises(ValueError, match="ODbL-1.0"):
        parse_feature(feature)


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
