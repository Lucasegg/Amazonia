"""Catálogo e regras determinísticas de consumo do inventário."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: str
    label: str
    description: str
    hunger_recovery: int = 0
    thirst_recovery: int = 0
    time_cost_minutes: int = 5


ITEMS: dict[str, Item] = {
    "agua_potavel": Item(
        id="agua_potavel",
        label="Água potável",
        description="Garrafa de água segura para consumo.",
        thirst_recovery=25,
    ),
    "racao": Item(
        id="racao",
        label="Ração de emergência",
        description="Alimento simples, compacto e não perecível.",
        hunger_recovery=20,
    ),
}


class InventoryRuleError(ValueError):
    """Ação incompatível com o inventário ou catálogo."""


def consume_item(
    inventory: list[str],
    needs: dict[str, int],
    item_id: str,
) -> tuple[list[str], dict[str, int], int]:
    """Consome uma unidade e retorna inventário, necessidades e tempo.

    IDs desconhecidos, itens não consumíveis ou unidades ausentes são rejeitados.
    A função é pura: persistência e atomicidade ficam a cargo da API.
    """
    item = ITEMS.get(item_id)
    if item is None:
        raise InventoryRuleError("Item não encontrado ou não consumível.")
    if item_id not in inventory:
        raise InventoryRuleError("Você não possui esse item no inventário.")

    updated_needs = {
        "hunger": min(100, max(0, int(needs.get("hunger", 0)))),
        "thirst": min(100, max(0, int(needs.get("thirst", 0)))),
        "fatigue": min(100, max(0, int(needs.get("fatigue", 0)))),
        "health": min(100, max(0, int(needs.get("health", 100)))),
    }
    updated_needs["hunger"] = max(0, updated_needs["hunger"] - item.hunger_recovery)
    updated_needs["thirst"] = max(0, updated_needs["thirst"] - item.thirst_recovery)

    updated_inventory = list(inventory)
    updated_inventory.remove(item_id)
    return updated_inventory, updated_needs, item.time_cost_minutes
