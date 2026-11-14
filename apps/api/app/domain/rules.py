"""Regras determinísticas iniciais do Amazonia.

O módulo não conhece HTTP, banco de dados ou provedor de IA. Isso permite
testar e evoluir o motor sem acoplar as regras à interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


ATTRIBUTES = ("vigor", "coordenacao", "percepcao", "raciocinio", "presenca")
SKILL_LEVEL_CAP = 5
PRACTICE_THRESHOLDS = (4, 8, 13, 19, 26)


class Origin(StrEnum):
    FIREFIGHTER = "bombeiro"
    HEALTH_WORKER = "profissional_de_saude"
    MECHANIC = "mecanico"


@dataclass(frozen=True)
class OriginProfile:
    id: Origin
    label: str
    starting_skills: Mapping[str, int]
    starting_items: tuple[str, ...]
    contextual_strength: str


ORIGINS: dict[Origin, OriginProfile] = {
    Origin.FIREFIGHTER: OriginProfile(
        id=Origin.FIREFIGHTER,
        label="Bombeiro",
        starting_skills={"primeiros_socorros": 1, "construcao_reparos": 1},
        starting_items=("kit_primeiros_socorros_basico", "ferramenta_resgate_simples"),
        contextual_strength="avaliação de riscos e resposta a emergências",
    ),
    Origin.HEALTH_WORKER: OriginProfile(
        id=Origin.HEALTH_WORKER,
        label="Profissional de saúde",
        starting_skills={"primeiros_socorros": 2, "investigacao_sintomas": 1},
        starting_items=("kit_atendimento_basico",),
        contextual_strength="reconhecimento de sinais clínicos e organização do atendimento",
    ),
    Origin.MECHANIC: OriginProfile(
        id=Origin.MECHANIC,
        label="Mecânico",
        starting_skills={"mecanica": 2, "ferramentas_manutencao": 1},
        starting_items=("conjunto_compacto_ferramentas",),
        contextual_strength="diagnóstico de defeitos e reparos com peças disponíveis",
    ),
}


class RuleValidationError(ValueError):
    """Entrada incompatível com as regras do jogo."""


@dataclass(frozen=True)
class CheckResult:
    roll: int
    attribute_modifier: int
    skill_level: int
    situational_modifier: int
    total: int
    difficulty: int
    success: bool
    margin: int
    outcome: str


def attribute_modifier(value: int) -> int:
    if not 1 <= value <= 5:
        raise RuleValidationError("Atributos devem estar entre 1 e 5.")
    return value - 3


def resolve_check(
    *,
    roll: int,
    attribute_value: int,
    skill_level: int,
    difficulty: int,
    situational_modifier: int = 0,
) -> CheckResult:
    """Resolve 1d20 + atributo-3 + habilidade + modificador situacional."""
    if not 1 <= roll <= 20:
        raise RuleValidationError("A rolagem do D20 deve estar entre 1 e 20.")
    if not 0 <= skill_level <= SKILL_LEVEL_CAP:
        raise RuleValidationError("Habilidade deve estar entre 0 e 5.")
    if difficulty not in (8, 12, 16, 20, 24):
        raise RuleValidationError("Dificuldade deve ser 8, 12, 16, 20 ou 24.")
    if not -2 <= situational_modifier <= 2:
        raise RuleValidationError("Modificador situacional deve estar entre -2 e +2.")

    modifier = attribute_modifier(attribute_value)
    total = roll + modifier + skill_level + situational_modifier
    margin = total - difficulty
    success = margin >= 0
    outcome = "sucesso_expressivo" if margin >= 5 else (
        "complicacao_relevante" if margin <= -5 else (
            "sucesso" if success else "falha"
        )
    )
    return CheckResult(
        roll=roll,
        attribute_modifier=modifier,
        skill_level=skill_level,
        situational_modifier=situational_modifier,
        total=total,
        difficulty=difficulty,
        success=success,
        margin=margin,
        outcome=outcome,
    )


def award_practice(
    *,
    current_level: int,
    current_points: int,
    event_key: str,
    already_awarded_events: frozenset[str],
    points: int,
) -> tuple[int, int, frozenset[str]]:
    """Concede prática uma única vez por evento significativo.

    Retorna (novo nível, pontos restantes, conjunto de eventos já usados).
    O chamador deve persistir o conjunto junto ao estado do personagem.
    """
    if not event_key.strip():
        raise RuleValidationError("O evento de prática precisa de identificador.")
    if not 0 <= current_level <= SKILL_LEVEL_CAP:
        raise RuleValidationError("Nível atual deve estar entre 0 e 5.")
    if current_points < 0:
        raise RuleValidationError("Pontos de prática não podem ser negativos.")
    if points not in (1, 2, 3):
        raise RuleValidationError("Prática significativa concede de 1 a 3 pontos.")
    if event_key in already_awarded_events or current_level == SKILL_LEVEL_CAP:
        return current_level, current_points, already_awarded_events

    level = current_level
    remaining = current_points + points
    awarded = already_awarded_events | {event_key}
    while level < SKILL_LEVEL_CAP and remaining >= PRACTICE_THRESHOLDS[level]:
        remaining -= PRACTICE_THRESHOLDS[level]
        level += 1
    return level, remaining, awarded
