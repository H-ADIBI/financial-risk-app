"""
Logistic-regression-based issuer distress model.

Trained on a synthetic dataset of financial ratios (leverage, interest
coverage, current ratio, profit margin) with a hand-crafted, plausible
relationship to a binary "distressed" label. This stands in for a real
model trained on actual issuer financials / historical defaults --
replace `_generate_training_data` with a loader for real data, or the
whole class with a different model class, without touching any other
part of the app (it's discovered by key: "logistic_regression").
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from risk_engine.credit.base import DistressModel, DistressResult
from risk_engine.data.models import Portfolio
from risk_engine.registry import register

FEATURES = ["leverage_ratio", "interest_coverage", "current_ratio", "profit_margin"]


def _generate_training_data(n: int = 2000, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    leverage = np.clip(rng.normal(0.45, 0.2, n), 0.02, 0.98)
    coverage = np.clip(rng.normal(4.5, 3.5, n), 0.05, 25.0)
    current_ratio = np.clip(rng.normal(1.3, 0.6, n), 0.2, 5.0)
    margin = np.clip(rng.normal(0.06, 0.1, n), -0.3, 0.4)

    # A hand-crafted "true" distress score: higher leverage, lower
    # coverage/current ratio/margin -> higher distress probability.
    logit = (
        3.2 * leverage
        - 0.35 * coverage
        - 0.9 * current_ratio
        - 4.0 * margin
        - 1.0
    )
    prob = 1 / (1 + np.exp(-logit))
    label = (rng.uniform(0, 1, n) < prob).astype(int)

    return pd.DataFrame(
        {
            "leverage_ratio": leverage,
            "interest_coverage": coverage,
            "current_ratio": current_ratio,
            "profit_margin": margin,
            "distressed": label,
        }
    )


@register("distress_model", "logistic_regression", description="Logistic regression issuer distress model")
class LogisticDistressModel(DistressModel):
    display_name = "Logistic Regression Distress Model"
    description = (
        "Predicts each holding's probability of financial distress from issuer-level "
        "ratios (leverage, interest coverage, current ratio, profit margin) using a "
        "logistic regression trained on synthetic data reflecting plausible relationships."
    )

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = LogisticRegression()
        self._fitted = False

    def fit(self, training_df: pd.DataFrame | None = None, **kwargs) -> "LogisticDistressModel":
        df = training_df if training_df is not None else _generate_training_data()
        X = self.scaler.fit_transform(df[FEATURES])
        y = df["distressed"]
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict(self, portfolio: Portfolio) -> DistressResult:
        if not self._fitted:
            self.fit()

        df = portfolio.to_dataframe()
        X = self.scaler.transform(df[FEATURES])
        proba = self.model.predict_proba(X)[:, 1]

        result_df = df[["position_id", "name", "sector", "asset_class", "market_value"]].copy()
        result_df["distress_probability"] = proba

        expected_distressed_value = float((result_df["market_value"] * result_df["distress_probability"]).sum())

        return DistressResult(
            model_key=self.registry_key,
            model_name=self.display_name,
            position_probabilities=result_df.sort_values("distress_probability", ascending=False),
            portfolio_expected_distressed_value=expected_distressed_value,
        )

    def coefficients(self) -> pd.Series:
        """Standardized coefficients, useful for explaining the model to
        the user / feeding the AI analyst a compact model summary."""
        if not self._fitted:
            self.fit()
        return pd.Series(self.model.coef_[0], index=FEATURES).sort_values(key=abs, ascending=False)
