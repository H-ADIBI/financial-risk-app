"""
Placeholder forecasting model: a random-walk-with-drift forecast, used
so the "forecast_model" category isn't empty and the wiring (registry ->
UI -> scenario shock_inputs) can be demonstrated end-to-end today.

To add ARIMAX later: create risk_engine/forecasting/arimax.py with a
class implementing ForecastModel (likely using statsmodels'
SARIMAX/ARIMA with exogenous regressors), decorate it with
@register("forecast_model", "arimax"), and it will appear next to this
one everywhere forecast models are selectable -- no changes needed here
or in the scenario/UI code.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from risk_engine.forecasting.base import ForecastModel, ForecastResult
from risk_engine.registry import register


@register("forecast_model", "naive_drift", description="Random-walk-with-drift placeholder forecaster")
class NaiveDriftForecast(ForecastModel):
    display_name = "Naive Drift Forecast (placeholder)"
    description = (
        "Simple random-walk-with-drift extrapolation of recent history. "
        "Stand-in for a more sophisticated model (e.g. ARIMAX) to be added later."
    )

    def forecast(self, history: pd.Series, horizon_periods: int, seed: int = 0, **kwargs) -> ForecastResult:
        drift = history.diff().dropna().mean() if len(history) > 1 else 0.0
        rng = np.random.default_rng(seed)
        noise_scale = history.diff().dropna().std() if len(history) > 1 else 0.0
        last_level = history.iloc[-1]

        path = []
        level = last_level
        for _ in range(horizon_periods):
            level = level + drift + rng.normal(0, noise_scale or 0.0)
            path.append(level)

        idx = pd.RangeIndex(1, horizon_periods + 1)
        forecast_series = pd.Series(path, index=idx, name=history.name or "forecast")
        return ForecastResult(
            variable=str(history.name or "series"),
            horizon_periods=horizon_periods,
            forecast=forecast_series,
        )
