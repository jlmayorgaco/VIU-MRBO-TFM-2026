"""Scenario registry for V6 experiments."""

from __future__ import annotations

from viu_mrob_tfm.scenarios.base import BaseScenario
from viu_mrob_tfm.scenarios.warehouse import WarehouseCoalitionScenario


def default_scenarios() -> dict[str, BaseScenario]:
    scenario = WarehouseCoalitionScenario()
    return {scenario.metadata.name: scenario}
