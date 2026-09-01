"""
OSFI-aligned macro stress scenarios.

These mirror the kind of scenario categories used in OSFI's stress
testing guidance (e.g. B-13 operational resilience context aside, and
the macro-financial scenario style used in IRRBB / EWST-type exercises):
an interest-rate shock, a credit-spread widening shock, an equity
market drawdown, and an FX shock -- plus one combined "severe adverse"
scenario that layers all four. These are illustrative magnitudes for a
demo app, not a reproduction of any specific published OSFI scenario;
treat the numbers as configurable placeholders.

Each scenario is a small, independent, registered class -- add a new
one (e.g. a housing-market shock, or a scenario driven by an ARIMAX
rate forecast via `shock_inputs`) by adding a new class here or a new
file in this folder.
"""
from __future__ import annotations

from risk_engine.data.models import Portfolio
from risk_engine.registry import register
from risk_engine.scenarios.base import ScenarioResult, StressScenario
from risk_engine.scenarios.shocks import apply_position_shocks


def _build_result(key: str, name: str, portfolio: Portfolio, pnl_df, shock_params: dict) -> ScenarioResult:
    base_value = portfolio.total_market_value
    shocked_value = base_value + pnl_df["pnl"].sum()
    return ScenarioResult(
        scenario_key=key,
        scenario_name=name,
        base_value=base_value,
        shocked_value=shocked_value,
        position_pnl=pnl_df,
        shock_parameters=shock_params,
    )


@register("scenario", "rate_shock_up", description="Parallel interest rate shock up")
class RateShockUp(StressScenario):
    display_name = "Interest Rate Shock (+200bps)"
    description = "Parallel upward shift in the yield curve, OSFI-style IRRBB shock."
    default_bps = 200

    def apply(self, portfolio: Portfolio, shock_inputs: dict | None = None) -> ScenarioResult:
        bps = (shock_inputs or {}).get("rate_shock_bps", self.default_bps)
        pnl_df = apply_position_shocks(portfolio, rate_shock_bps=bps)
        return _build_result(self.registry_key, self.display_name, portfolio, pnl_df, {"rate_shock_bps": bps})


@register("scenario", "credit_spread_widening", description="Corporate credit spread widening")
class CreditSpreadWidening(StressScenario):
    display_name = "Credit Spread Widening (+150bps)"
    description = "Widening of corporate credit spreads, consistent with a credit-cycle downturn scenario."
    default_bps = 150

    def apply(self, portfolio: Portfolio, shock_inputs: dict | None = None) -> ScenarioResult:
        bps = (shock_inputs or {}).get("credit_spread_shock_bps", self.default_bps)
        pnl_df = apply_position_shocks(portfolio, credit_spread_shock_bps=bps)
        return _build_result(
            self.registry_key, self.display_name, portfolio, pnl_df, {"credit_spread_shock_bps": bps}
        )


@register("scenario", "equity_drawdown", description="Broad equity market drawdown")
class EquityMarketDrawdown(StressScenario):
    display_name = "Equity Market Drawdown (-30%)"
    description = "Sharp broad-based equity market correction, akin to a severe recession scenario."
    default_pct = -0.30

    def apply(self, portfolio: Portfolio, shock_inputs: dict | None = None) -> ScenarioResult:
        pct = (shock_inputs or {}).get("equity_shock_pct", self.default_pct)
        pnl_df = apply_position_shocks(portfolio, equity_shock_pct=pct)
        return _build_result(self.registry_key, self.display_name, portfolio, pnl_df, {"equity_shock_pct": pct})


@register("scenario", "fx_shock", description="Sharp depreciation of foreign currencies vs. base currency")
class FXShock(StressScenario):
    display_name = "FX Shock (-15% vs. base currency)"
    description = "Sharp move in FX rates against the portfolio's base currency."
    default_pct = -0.15

    def apply(self, portfolio: Portfolio, shock_inputs: dict | None = None) -> ScenarioResult:
        pct = (shock_inputs or {}).get("fx_shock_pct", self.default_pct)
        pnl_df = apply_position_shocks(portfolio, fx_shock_pct=pct)
        return _build_result(self.registry_key, self.display_name, portfolio, pnl_df, {"fx_shock_pct": pct})


@register("scenario", "severe_adverse", description="Combined severe adverse macro scenario (all shocks layered)")
class SevereAdverseScenario(StressScenario):
    display_name = "Severe Adverse Scenario (Combined)"
    description = (
        "Combined macro-financial stress: rate shock + credit spread widening + "
        "equity drawdown + FX shock applied simultaneously, in the spirit of an "
        "OSFI-style enterprise-wide severe adverse scenario."
    )
    defaults = {
        "rate_shock_bps": 200,
        "credit_spread_shock_bps": 200,
        "equity_shock_pct": -0.40,
        "fx_shock_pct": -0.20,
    }

    def apply(self, portfolio: Portfolio, shock_inputs: dict | None = None) -> ScenarioResult:
        params = {**self.defaults, **(shock_inputs or {})}
        pnl_df = apply_position_shocks(
            portfolio,
            rate_shock_bps=params["rate_shock_bps"],
            credit_spread_shock_bps=params["credit_spread_shock_bps"],
            equity_shock_pct=params["equity_shock_pct"],
            fx_shock_pct=params["fx_shock_pct"],
        )
        return _build_result(self.registry_key, self.display_name, portfolio, pnl_df, params)
