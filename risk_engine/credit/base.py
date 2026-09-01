"""Interface for a distress/default-probability model. See
risk_engine/registry.py for how implementations plug into the app."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from risk_engine.data.models import Portfolio


@dataclass
class DistressResult:
    model_key: str
    model_name: str
    position_probabilities: pd.DataFrame  # position_id, name, sector, distress_probability
    portfolio_expected_distressed_value: float


class DistressModel(ABC):
    display_name: str = "Unnamed distress model"
    description: str = ""

    @abstractmethod
    def fit(self, **kwargs) -> "DistressModel":
        raise NotImplementedError

    @abstractmethod
    def predict(self, portfolio: Portfolio) -> DistressResult:
        raise NotImplementedError
