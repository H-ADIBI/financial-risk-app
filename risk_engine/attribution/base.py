"""Interface for a risk attribution method. See risk_engine/registry.py
for how implementations plug into the app."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from risk_engine.data.models import Portfolio
from risk_engine.var.base import VaRResult


@dataclass
class AttributionResult:
    model_key: str
    model_name: str
    by_position: pd.DataFrame   # position_id, name, sector, component_var, pct_of_var
    by_sector: pd.DataFrame     # sector, component_var, pct_of_var
    by_asset_class: pd.DataFrame


class AttributionModel(ABC):
    display_name: str = "Unnamed attribution model"
    description: str = ""

    @abstractmethod
    def compute(self, portfolio: Portfolio, var_result: VaRResult) -> AttributionResult:
        raise NotImplementedError
