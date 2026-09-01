"""
PortfolioSource implementations: the extension point for "where does
portfolio data come from". Each class here registers itself under the
"portfolio_source" category (see risk_engine/registry.py) so the UI and
AI analyst can discover it by key without any other code changes.

Today the app ships "random" and "csv". Adding a third source (say, a
live pull from a custodian API) means adding a new class in this file
(or a new file in this folder) with @register("portfolio_source", "your_key")
-- nothing in app/pages or the rest of the risk engine needs to change.
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd

from risk_engine.config import ASSET_CLASSES, CONFIG, SECTORS
from risk_engine.data.base import PortfolioSource
from risk_engine.data.models import Portfolio, Position
from risk_engine.registry import register


@register("portfolio_source", "random", description="Randomly generated diversified sample portfolio")
class RandomPortfolioSource(PortfolioSource):
    """Generates a plausible, diversified synthetic portfolio.

    This is what the app uses out of the box so it's demoable with zero
    setup. The randomness is seeded by default for reproducibility, but
    callers can pass a different seed to get a fresh book.
    """

    display_name = "Random Sample Portfolio"

    def load(
        self,
        num_positions: int = CONFIG.default_num_positions,
        total_value: float = CONFIG.default_portfolio_value,
        seed: int | None = CONFIG.random_seed,
        name: str = "Sample Diversified Portfolio",
    ) -> Portfolio:
        rng = np.random.default_rng(seed)

        # Random raw weights (Dirichlet gives us positive weights that sum to 1)
        raw_weights = rng.dirichlet(np.ones(num_positions) * 1.5)
        market_values = raw_weights * total_value

        positions = []
        for i in range(num_positions):
            asset_class = rng.choice(ASSET_CLASSES, p=[0.45, 0.25, 0.20, 0.10])
            sector = rng.choice(SECTORS) if asset_class != "FX" else "N/A"

            if asset_class == "Equity":
                vol = rng.uniform(0.15, 0.45)
                beta = rng.uniform(0.6, 1.6)
                duration = 0.0
                spread_dur = 0.0
                fx_sens = rng.uniform(-0.2, 0.2)
            elif asset_class == "Corporate Bond":
                vol = rng.uniform(0.03, 0.10)
                beta = rng.uniform(0.0, 0.15)
                duration = rng.uniform(1.5, 9.0)
                spread_dur = duration * rng.uniform(0.8, 1.1)
                fx_sens = rng.uniform(-0.1, 0.1)
            elif asset_class == "Government Bond":
                vol = rng.uniform(0.02, 0.07)
                beta = 0.0
                duration = rng.uniform(1.0, 15.0)
                spread_dur = 0.0
                fx_sens = rng.uniform(-0.05, 0.05)
            else:  # FX
                vol = rng.uniform(0.05, 0.12)
                beta = 0.0
                duration = 0.0
                spread_dur = 0.0
                fx_sens = rng.uniform(0.7, 1.3)

            positions.append(
                Position(
                    position_id=f"POS-{i+1:04d}",
                    name=f"{asset_class} Holding {i+1}",
                    asset_class=asset_class,
                    sector=sector,
                    market_value=float(market_values[i]),
                    expected_return=float(rng.uniform(0.01, 0.08)),
                    volatility=float(vol),
                    duration=float(duration),
                    credit_spread_dur=float(spread_dur),
                    equity_beta=float(beta),
                    fx_sensitivity=float(fx_sens),
                    leverage_ratio=float(np.clip(rng.normal(0.4, 0.15), 0.05, 0.9)),
                    interest_coverage=float(np.clip(rng.normal(5.0, 3.0), 0.2, 20.0)),
                    current_ratio=float(np.clip(rng.normal(1.4, 0.5), 0.3, 4.0)),
                    profit_margin=float(np.clip(rng.normal(0.08, 0.08), -0.15, 0.35)),
                )
            )

        return Portfolio(name=name, positions=positions)


@register("portfolio_source", "csv", description="Upload your own positions as a CSV file")
class CSVPortfolioSource(PortfolioSource):
    """Load a Portfolio from an uploaded CSV.

    Expected columns (extra columns are ignored, missing optional ones
    fall back to Position defaults):
        position_id, name, asset_class, sector, market_value,
        expected_return, volatility, duration, credit_spread_dur,
        equity_beta, fx_sensitivity, leverage_ratio, interest_coverage,
        current_ratio, profit_margin

    This is intentionally already wired up end-to-end -- the Portfolio
    page's file_uploader can call this today. Harden it further (schema
    validation, better error messages, unit conversion) as your real
    data feeds come online.
    """

    display_name = "Upload CSV"

    def load(self, file: io.BytesIO | str, name: str = "Uploaded Portfolio") -> Portfolio:
        df = pd.read_csv(file)
        required = {"name", "asset_class", "sector", "market_value"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
        if "position_id" not in df.columns:
            df["position_id"] = [f"POS-{i+1:04d}" for i in range(len(df))]
        return Portfolio.from_dataframe(name=name, df=df)
