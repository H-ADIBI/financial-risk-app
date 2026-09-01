"""
Synthetic market data: a correlation structure and return draws used by
the Monte Carlo VaR engine. Swappable later for a real market data feed
(e.g. Bloomberg, Refinitiv, or a vendor API) as long as the replacement
returns a correlation matrix indexed the same way.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from risk_engine.data.models import Portfolio


def build_correlation_matrix(portfolio: Portfolio, seed: int = 7) -> pd.DataFrame:
    """Build a plausible correlation matrix across the portfolio's positions.

    Positions in the same sector/asset class are given higher correlation
    to mimic real-world clustering; a small amount of idiosyncratic noise
    is added elsewhere. The result is forced to be positive semi-definite.
    """
    df = portfolio.to_dataframe()
    n = len(df)
    rng = np.random.default_rng(seed)

    corr = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            same_sector = df.iloc[i]["sector"] == df.iloc[j]["sector"]
            same_asset_class = df.iloc[i]["asset_class"] == df.iloc[j]["asset_class"]
            base = 0.55 if same_sector else (0.25 if same_asset_class else 0.08)
            noise = rng.normal(0, 0.05)
            corr[i, j] = corr[j, i] = float(np.clip(base + noise, -0.2, 0.9))

    # Nudge to the nearest positive semi-definite matrix (numerically safe
    # for Cholesky-based simulation).
    eigvals, eigvecs = np.linalg.eigh(corr)
    eigvals = np.clip(eigvals, 1e-6, None)
    corr_psd = eigvecs @ np.diag(eigvals) @ eigvecs.T
    d = np.sqrt(np.diag(corr_psd))
    corr_psd = corr_psd / np.outer(d, d)
    np.fill_diagonal(corr_psd, 1.0)

    ids = df["position_id"].tolist()
    return pd.DataFrame(corr_psd, index=ids, columns=ids)
