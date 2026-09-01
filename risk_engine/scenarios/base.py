"""Interface for a stress scenario. See risk_engine/registry.py for how
implementations plug into the app."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd

from risk_engine.data.models import Portfolio


@dataclass
class ScenarioResult:
    scenario_key: str
    scenario_name: str
    base_value: float
    shocked_value: float
    position_pnl: pd.DataFrame          # per-position P&L breakdown
    shock_parameters: dict = field(default_factory=dict)

    @property
    def total_pnl(self) -> float:
        return self.shocked_value - self.base_value

    @property
    def total_pnl_pct(self) -> float:
        return self.total_pnl / self.base_value if self.base_value else 0.0


class StressScenario(ABC):
    """A named, parameterized shock applied to a Portfolio.

    `shock_inputs` lets a scenario's magnitudes come from somewhere other
    than a hardcoded table -- e.g. an OSFI-published severe scenario, a
    user-adjusted slider in the UI, or (future extension) the output of a
    forecasting model such as an ARIMAX interest-rate forecast registered
    under the "forecast_model" category. Implementations should accept an
    optional `shock_inputs` override and fall back to their own defaults.
    """

    display_name: str = "Unnamed scenario"
    description: str = ""

    @abstractmethod
    def apply(self, portfolio: Portfolio, shock_inputs: dict | None = None) -> ScenarioResult:
        raise NotImplementedError
