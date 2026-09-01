"""
Core data models shared across the whole risk engine.

Everything downstream (scenarios, VaR, distress model, attribution,
the AI analyst tools, and the Streamlit UI) works with a `Portfolio`
of `Position` objects. As long as a data source produces a `Portfolio`,
it doesn't matter whether the positions came from a random generator
or a CSV upload -- that's the extension point described in sources.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class Position:
    position_id: str
    name: str
    asset_class: str          # e.g. "Equity", "Corporate Bond", "Government Bond", "FX"
    sector: str                # e.g. "Financials", "Energy", ...
    market_value: float        # current market value in portfolio base currency
    weight: float = 0.0        # fraction of portfolio market value (filled in by Portfolio)

    # Return-model parameters (annualized), used by Monte Carlo VaR
    expected_return: float = 0.0
    volatility: float = 0.15

    # Sensitivities used by the OSFI stress scenarios
    duration: float = 0.0          # interest-rate duration (bonds); 0 for equities/FX
    credit_spread_dur: float = 0.0  # spread duration (corporate bonds); 0 otherwise
    equity_beta: float = 0.0        # sensitivity to broad equity market shock
    fx_sensitivity: float = 0.0     # sensitivity to a 1% move in the relevant FX pair

    # Fields consumed by the logistic-regression distress model.
    # These stand in for issuer/company financial ratios and are only
    # meaningful for credit-risk-bearing positions (bonds); default to
    # benign values for equities/FX so the model still runs on any book.
    leverage_ratio: float = 0.3        # debt / assets
    interest_coverage: float = 6.0     # EBIT / interest expense
    current_ratio: float = 1.5         # current assets / current liabilities
    profit_margin: float = 0.08

    def as_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Portfolio:
    name: str
    base_currency: str = "USD"
    positions: list[Position] = field(default_factory=list)

    def __post_init__(self):
        self._recompute_weights()

    def _recompute_weights(self):
        total = self.total_market_value
        if total > 0:
            for p in self.positions:
                p.weight = p.market_value / total

    @property
    def total_market_value(self) -> float:
        return sum(p.market_value for p in self.positions)

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame([p.as_dict() for p in self.positions])
        return df

    def sector_exposure(self) -> pd.Series:
        df = self.to_dataframe()
        if df.empty:
            return pd.Series(dtype=float)
        return df.groupby("sector")["market_value"].sum().sort_values(ascending=False)

    def asset_class_exposure(self) -> pd.Series:
        df = self.to_dataframe()
        if df.empty:
            return pd.Series(dtype=float)
        return df.groupby("asset_class")["market_value"].sum().sort_values(ascending=False)

    @classmethod
    def from_dataframe(cls, name: str, df: pd.DataFrame, base_currency: str = "USD") -> "Portfolio":
        """Build a Portfolio from a DataFrame (e.g. an uploaded CSV).

        Expected columns match the Position fields; any missing optional
        columns fall back to Position's defaults. This is the seam the
        future CSVPortfolioSource will use.
        """
        positions = []
        for _, row in df.iterrows():
            kwargs = {k: v for k, v in row.to_dict().items() if k in Position.__dataclass_fields__}
            positions.append(Position(**kwargs))
        return cls(name=name, base_currency=base_currency, positions=positions)
