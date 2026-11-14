from app.domain.world import (
    HEX_RADIUS_METERS,
    ORIGIN_LATITUDE,
    ORIGIN_LONGITUDE,
    POI_CATALOG,
    build_map_data,
    cell_center,
    hex_distance,
    latlon_to_cell,
)


class FakeCampaign:
    id = "campaign-1"
    world_time_minutes = 10


class FakeCharacter:
    position_q = 1
    position_r = 0
    discovered_cells = ["0:0", "1:0"]


def test_hex_distance_recognizes_adjacent_cells():
    assert hex_distance(0, 0, 1, 0) == 1
    assert hex_distance(0, 0, 1, -1) == 1
    assert hex_distance(0, 0, 2, 0) == 2


def test_cell_center_returns_sao_paulo_reference_at_origin():
    latitude, longitude = cell_center(0, 0)
    assert latitude == -23.5505
    assert longitude == -46.6333


def test_map_only_marks_discovered_cells_and_current_position():
    result = build_map_data(FakeCampaign(), FakeCharacter())
    current = next(cell for cell in result["cells"] if cell["current"])
    start = next(cell for cell in result["cells"] if cell["q"] == 0 and cell["r"] == 0)
    assert current["discovered"] is True
    assert current["latitude"] != 0
    assert start["discovered"] is True
    assert len(result["cells"]) == 19
    assert result["hex_radius_meters"] == HEX_RADIUS_METERS


def test_hex_origin_round_trips_to_axial_zero():
    """A origem geográfica do mapa corresponde à célula axial 0:0."""
    assert latlon_to_cell(ORIGIN_LATITUDE, ORIGIN_LONGITUDE) == (0, 0)


def test_municipal_coordinates_map_to_expected_cells():
    """Pontos próximos ao Centro são atribuídos às células previstas."""
    assert latlon_to_cell(-23.55037, -46.63395) == (0, 0)
    assert latlon_to_cell(-23.54807, -46.63295) == (0, 0)
    assert latlon_to_cell(-23.54176, -46.62939) == (0, 1)
    assert latlon_to_cell(-23.545424, -46.627899) == (0, 1)


def test_cell_centers_round_trip_for_initial_neighborhood():
    """Centros da grade inicial retornam à mesma coordenada axial."""
    for q, r in ((0, 0), (1, 0), (0, 1), (-1, 1), (-2, 0), (1, -2)):
        latitude, longitude = cell_center(q, r)
        assert latlon_to_cell(latitude, longitude) == (q, r)


def test_poi_catalog_has_unique_ids_and_valid_coordinates():
    """Catálogo municipal tem IDs únicos e coordenadas na região de São Paulo."""
    ids = [str(poi["id"]) for poi in POI_CATALOG]
    assert len(ids) == len(set(ids))
    for poi in POI_CATALOG:
        assert -24.0 < float(poi["latitude"]) < -23.0
        assert -47.0 < float(poi["longitude"]) < -46.0


def test_map_only_returns_pois_in_discovered_cells():
    """POIs de células não descobertas permanecem ocultos."""
    result = build_map_data(FakeCampaign(), FakeCharacter())
    ids = {poi["id"] for poi in result["points_of_interest"]}
    assert ids == {"praca_se", "pateo_do_colegio"}
    assert "mercado_municipal" not in ids
