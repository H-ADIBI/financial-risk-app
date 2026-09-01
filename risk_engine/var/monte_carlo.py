"""
Monte Carlo VaR / CVaR via correlated multivariate-normal return
simulation. This is the "lightweight but real" version: it correctly
simulates correlated position-level returns, aggregates to portfolio
P&L, and computes VaR/CVaR at each requested confidence level, but uses
a normal-returns assumption rather than fat-tailed / copula-based
simulation. Swap the sampling step below for a Student-t copula, a
GARCH-filtered historical simulation, etc. as you harden this.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from risk_engine.data.market_data import build_correlation_matrix
from risk_engine.data.models import Portfolio
from risk_engine.registry import register
from risk_engine.var.base import VaRModel, VaRResult


@register("var_model", "monte_carlo", description="Correlated Monte Carlo simulation VaR/CVaR")
class MonteCarloVaR(VaRModel):
    display_name = "Monte Carlo VaR"
    description = (
        "Simulates correlated position-level returns over the horizon using each "
        "position's volatility and a sector/asset-class-implied correlation matrix, "
        "then computes portfolio VaR and CVaR (Expected Shortfall) from the simulated "
        "P&L distribution."
    )

    def compute(
        self,
        portfolio: Portfolio,
        confidence_levels: tuple = (0.95, 0.99),
        horizon_days: int = 10,
        num_simulations: int = 10_000,
        seed: int = 123,
        **kwargs,
    ) -> VaRResult:
        df = portfolio.to_dataframe()
        n = len(df)
        if n == 0:
            raise ValueError("Portfolio has no positions.")

        corr = build_correlation_matrix(portfolio).values
        vols_annual = df["volatility"].to_numpy()
        mus_annual = df["expected_return"].to_numpy()
        values = df["market_value"].to_numpy()

        dt = horizon_days / 252.0
        vols_h = vols_annual * np.sqrt(dt)
        mus_h = mus_annual * dt

        cov_h = np.outer(vols_h, vols_h) * corr
        # Guard against tiny negative eigenvalues from floating point noise
        cov_h = (cov_h + cov_h.T) / 2.0

        rng = np.random.default_rng(seed)
        sim_returns = rng.multivariate_normal(mean=mus_h, cov=cov_h, size=num_simulations)

        sim_position_pnl = sim_returns * values  # (num_simulations x n) dollar P&L per position
        sim_portfolio_pnl = sim_position_pnl.sum(axis=1)

        var_by_conf, cvar_by_conf = {}, {}
        for cl in confidence_levels:
            loss_quantile = np.percentile(sim_portfolio_pnl, (1 - cl) * 100)
            var_amount = -loss_quantile  # positive number = loss
            tail_losses = sim_portfolio_pnl[sim_portfolio_pnl <= loss_quantile]
            cvar_amount = -tail_losses.mean() if len(tail_losses) > 0 else var_amount
            var_by_conf[cl] = float(var_amount)
            cvar_by_conf[cl] = float(cvar_amount)

        sim_position_pnl_df = pd.DataFrame(sim_position_pnl, columns=df["position_id"].tolist())

        return VaRResult(
            model_key=self.registry_key,
            model_name=self.display_name,
            horizon_days=horizon_days,
            confidence_levels=confidence_levels,
            portfolio_value=portfolio.total_market_value,
            simulated_pnl=sim_portfolio_pnl,
            var_by_confidence=var_by_conf,
            cvar_by_confidence=cvar_by_conf,
            simulated_position_pnl=sim_position_pnl_df,
        )
