"""Interface for a VaR/CVaR model. See risk_engine/registry.py for how
implementations plug into the app."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from risk_engine.data.models import Portfolio


@dataclass
class VaRResult:
    model_key: str
    model_name: str
    horizon_days: int
    confidence_levels: tuple
    portfolio_value: float
    simulated_pnl: np.ndarray                    # raw simulated portfolio P&L distribution
    var_by_confidence: dict[float, float] = field(default_factory=dict)     # positive number = loss
    cvar_by_confidence: dict[float, float] = field(default_factory=dict)    # positive number = loss
    simulated_position_pnl: pd.DataFrame | None = None  # sims x positions, for attribution


class VaRModel(ABC):
    display_name: str = "Unnamed VaR model"
    description: str = ""

    @abstractmethod
    def compute(
        self,
        portfolio: Portfolio,
        confidence_levels: tuple = (0.95, 0.99),
        horizon_days: int = 10,
        **kwargs,
    ) -> VaRResult:
        raise NotImplementedError
