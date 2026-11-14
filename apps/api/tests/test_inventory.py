from app.domain.inventory import InventoryRuleError, consume_item


def test_water_reduces_thirst_and_is_removed_once():
    inventory, needs, time_cost = consume_item(
        ["agua_potavel", "racao"],
        {"hunger": 15, "thirst": 40, "fatigue": 10, "health": 100},
        "agua_potavel",
    )
    assert inventory == ["racao"]
    assert needs == {"hunger": 15, "thirst": 15, "fatigue": 10, "health": 100}
    assert time_cost == 5


def test_food_reduces_hunger_without_changing_other_needs():
    inventory, needs, time_cost = consume_item(
        ["racao"],
        {"hunger": 30, "thirst": 12, "fatigue": 20, "health": 90},
        "racao",
    )
    assert inventory == []
    assert needs == {"hunger": 10, "thirst": 12, "fatigue": 20, "health": 90}
    assert time_cost == 5


def test_consumption_does_not_reduce_needs_below_zero():
    _, needs, _ = consume_item(
        ["racao"],
        {"hunger": 5, "thirst": 0, "fatigue": 0, "health": 100},
        "racao",
    )
    assert needs["hunger"] == 0


def test_unknown_or_missing_items_are_rejected():
    try:
        consume_item(["racao"], {"hunger": 10}, "item_inexistente")
    except InventoryRuleError as exc:
        assert "não encontrado" in str(exc)
    else:
        raise AssertionError("Item desconhecido deveria ser rejeitado.")

    try:
        consume_item([], {"hunger": 10}, "racao")
    except InventoryRuleError as exc:
        assert "não possui" in str(exc)
    else:
        raise AssertionError("Item ausente deveria ser rejeitado.")
