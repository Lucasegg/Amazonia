"""Motor determinístico de testes e pacotes de profissão."""
from dataclasses import dataclass
from random import SystemRandom

PROFESSIONS = {
    "firefighter": {"label": "Bombeiro", "skills": {"first_aid": 1, "construction_repair": 1}},
    "healthcare": {"label": "Profissional de saúde", "skills": {"first_aid": 2, "symptom_investigation": 1}},
    "mechanic": {"label": "Mecânico", "skills": {"mechanics": 2, "tool_use": 1}},
}
DEFAULT_ATTRIBUTES = {"vigor": 3, "coordination": 3, "perception": 3, "reasoning": 3, "presence": 3}

@dataclass(frozen=True)
class RollResult:
    """Resultado imutável de uma rolagem."""
    die: int
    attribute_modifier: int
    skill_level: int
    situational_modifier: int
    total: int
    difficulty: int
    outcome: str

def initial_skills(profession: str) -> dict[str, int]:
    """Retorna cópia do pacote inicial da profissão."""
    if profession not in PROFESSIONS:
        raise ValueError("Profissão não disponível no protótipo.")
    return dict(PROFESSIONS[profession]["skills"])

def resolve_roll(*, die: int, attribute_value: int, skill_level: int, difficulty: int, situational_modifier: int = 0) -> RollResult:
    """Resolve d20 + atributo menos três + habilidade + modificador."""
    if not 1 <= die <= 20 or not 1 <= attribute_value <= 5 or not 0 <= skill_level <= 5:
        raise ValueError("Dado, atributo ou habilidade fora dos limites.")
    if not 1 <= difficulty <= 30 or not -2 <= situational_modifier <= 2:
        raise ValueError("Dificuldade ou modificador fora dos limites.")
    attr_mod = attribute_value - 3
    total = die + attr_mod + skill_level + situational_modifier
    margin = total - difficulty
    outcome = "strong_success" if margin >= 5 else "success" if margin >= 0 else "complication" if margin <= -5 else "failure"
    return RollResult(die, attr_mod, skill_level, situational_modifier, total, difficulty, outcome)

def roll_d20() -> int:
    """Gera um d20 no servidor."""
    return SystemRandom().randint(1, 20)
