from app.domain.world import (
    HEX_RADIUS_METERS,
    build_map_data,
    cell_center,
    hex_distance,
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
