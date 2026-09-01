"""
Shared shock-application math used by every scenario in osfi_scenarios.py.

Kept separate from the scenario definitions themselves so new scenarios
can reuse (or override) the same first-order sensitivity approximations
instead of re-deriving repricing logic each time.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from risk_engine.data.models import Portfolio


def apply_position_shocks(
    portfolio: Portfolio,
    rate_shock_bps: float = 0.0,
    credit_spread_shock_bps: float = 0.0,
    equity_shock_pct: float = 0.0,
    fx_shock_pct: float = 0.0,
) -> pd.DataFrame:
    """First-order (duration/beta/sensitivity) repricing of every position
    under a combined macro shock. Returns a DataFrame with pre/post values
    and P&L per position.

    This is deliberately a linear approximation (duration x rate shock,
    beta x equity shock, etc.) rather than a full repricing model -- good
    enough to demonstrate scenario mechanics end-to-end; swap in real
    pricing functions per asset class as you harden this.
    """
    rows = []
    for p in portfolio.positions:
        rate_effect = -p.duration * (rate_shock_bps / 10_000.0)
        credit_effect = -p.credit_spread_dur * (credit_spread_shock_bps / 10_000.0)
        equity_effect = p.equity_beta * equity_shock_pct
        fx_effect = p.fx_sensitivity * fx_shock_pct

        total_pct_change = rate_effect + credit_effect + equity_effect + fx_effect
        shocked_value = p.market_value * (1 + total_pct_change)

        rows.append(
            {
                "position_id": p.position_id,
                "name": p.name,
                "asset_class": p.asset_class,
                "sector": p.sector,
                "base_value": p.market_value,
                "shocked_value": shocked_value,
                "pnl": shocked_value - p.market_value,
                "pct_change": total_pct_change,
                "rate_effect": rate_effect * p.market_value,
                "credit_effect": credit_effect * p.market_value,
                "equity_effect": equity_effect * p.market_value,
                "fx_effect": fx_effect * p.market_value,
            }
        )
    return pd.DataFrame(rows)
