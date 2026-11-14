import pytest

from app.domain.rules import (
    RuleValidationError,
    award_practice,
    attribute_modifier,
    resolve_check,
)


def test_attribute_modifier_uses_three_as_average():
    assert attribute_modifier(1) == -2
    assert attribute_modifier(3) == 0
    assert attribute_modifier(5) == 2


def test_check_calculates_total_and_success():
    result = resolve_check(
        roll=12,
        attribute_value=4,
        skill_level=2,
        difficulty=16,
        situational_modifier=1,
    )
    assert result.total == 16
    assert result.success is True
    assert result.outcome == "sucesso"


def test_check_identifies_expressive_success():
    result = resolve_check(
        roll=20,
        attribute_value=5,
        skill_level=3,
        difficulty=20,
    )
    assert result.success is True
    assert result.outcome == "sucesso_expressivo"


def test_check_rejects_invalid_die_roll():
    with pytest.raises(RuleValidationError):
        resolve_check(
            roll=0,
            attribute_value=3,
            skill_level=0,
            difficulty=12,
        )


def test_practice_advances_level_and_carries_excess():
    level, points, events = award_practice(
        current_level=0,
        current_points=3,
        event_key="repair-001",
        already_awarded_events=frozenset(),
        points=2,
    )
    assert (level, points) == (1, 1)
    assert "repair-001" in events


def test_same_event_cannot_award_practice_twice():
    previous = frozenset({"repair-001"})
    result = award_practice(
        current_level=0,
        current_points=2,
        event_key="repair-001",
        already_awarded_events=previous,
        points=3,
    )
    assert result == (0, 2, previous)


def test_skill_level_five_is_a_hard_cap():
    level, points, events = award_practice(
        current_level=5,
        current_points=0,
        event_key="mastery-attempt",
        already_awarded_events=frozenset(),
        points=3,
    )
    assert (level, points, events) == (5, 0, frozenset())
