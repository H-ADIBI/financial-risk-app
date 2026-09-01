"""
Interface for a forecasting model whose output can feed into a stress
scenario as a shock input, instead of the scenario using a fixed
constant (e.g. "+200bps").

This is the seam for your planned interest-rate forecaster: implement
`ForecastModel.forecast()` with, say, an ARIMAX model trained on a rate
time series (plus exogenous drivers), register it under
("forecast_model", "arimax"), and any scenario can then be run with
`shock_inputs={"rate_shock_bps": forecast_model.forecast_shock_bps()}`
pulled from that model instead of the scenario's own default. Nothing
in the scenario base classes needs to change to support this -- they
already accept an arbitrary `shock_inputs` dict.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class ForecastResult:
    variable: str                # e.g. "10Y_rate", "USD_rate"
    horizon_periods: int
    forecast: pd.Series          # forecasted path, indexed by period
    lower_ci: pd.Series | None = None
    upper_ci: pd.Series | None = None

    def implied_shock(self, from_level: float | None = None) -> float:
        """Convenience: total change from the first forecast point (or a
        supplied current level) to the final forecast point -- the kind
        of scalar a stress scenario's shock_inputs would consume."""
        start = from_level if from_level is not None else self.forecast.iloc[0]
        return float(self.forecast.iloc[-1] - start)


class ForecastModel(ABC):
    display_name: str = "Unnamed forecast model"
    description: str = ""

    @abstractmethod
    def forecast(self, history: pd.Series, horizon_periods: int, **kwargs) -> ForecastResult:
        raise NotImplementedError
