"""
LangChain tools exposing the risk engine to the AI analyst agent.

Each tool works against whatever Portfolio is currently loaded in the
Streamlit session (set via ai_analyst.tools.set_active_portfolio before
invoking the agent) and dispatches through risk_engine.registry, so a
new scenario/VaR/distress/attribution model you register anywhere in
risk_engine becomes callable by the AI analyst without any changes here
-- the tool functions ask the registry "what's available" rather than
hardcoding a model list.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool

import risk_engine.data  # noqa: F401 -- triggers auto-discovery
import risk_engine.scenarios  # noqa: F401
import risk_engine.var  # noqa: F401
import risk_engine.credit  # noqa: F401
import risk_engine.attribution  # noqa: F401
from risk_engine import registry
from risk_engine.data.models import Portfolio

# Module-level "current context" the tools operate on. Streamlit sets this
# once per session before invoking the agent (see app/pages/6_AI_Analyst.py).
_ACTIVE_PORTFOLIO: Portfolio | None = None


def set_active_portfolio(portfolio: Portfolio) -> None:
    global _ACTIVE_PORTFOLIO
    _ACTIVE_PORTFOLIO = portfolio


def _require_portfolio() -> Portfolio:
    if _ACTIVE_PORTFOLIO is None:
        raise RuntimeError("No portfolio is loaded. Load one on the Portfolio page first.")
    return _ACTIVE_PORTFOLIO


@tool
def list_available_models() -> str:
    """List every risk model currently registered in the app, grouped by
    category (portfolio_source, scenario, var_model, distress_model,
    attribution_model, forecast_model). Call this first if you're unsure
    what analyses are available -- new models may have been added since
    you last checked."""
    return json.dumps(registry.all_categories(), indent=2)


@tool
def get_portfolio_summary() -> str:
    """Get a summary of the currently loaded portfolio: total market
    value, number of positions, and exposure by sector and asset class."""
    p = _require_portfolio()
    return json.dumps(
        {
            "name": p.name,
            "base_currency": p.base_currency,
            "total_market_value": p.total_market_value,
            "num_positions": len(p.positions),
            "sector_exposure": p.sector_exposure().round(2).to_dict(),
            "asset_class_exposure": p.asset_class_exposure().round(2).to_dict(),
        },
        indent=2,
    )


@tool
def run_stress_scenario(scenario_key: str, shock_overrides_json: str = "{}") -> str:
    """Run a registered stress scenario against the current portfolio.

    Args:
        scenario_key: key of the scenario, from list_available_models()'s
            "scenario" category (e.g. "rate_shock_up", "severe_adverse").
        shock_overrides_json: optional JSON object overriding that
            scenario's default shock magnitudes, e.g. '{"rate_shock_bps": 300}'.
    """
    p = _require_portfolio()
    overrides = json.loads(shock_overrides_json) if shock_overrides_json else {}
    scenario = registry.create("scenario", scenario_key)
    result = scenario.apply(p, shock_inputs=overrides)
    return json.dumps(
        {
            "scenario": result.scenario_name,
            "shock_parameters": result.shock_parameters,
            "base_value": result.base_value,
            "shocked_value": result.shocked_value,
            "total_pnl": result.total_pnl,
            "total_pnl_pct": result.total_pnl_pct,
            "top_5_losers": result.position_pnl.nsmallest(5, "pnl")[
                ["name", "sector", "pnl", "pct_change"]
            ].to_dict(orient="records"),
        },
        indent=2,
        default=str,
    )


@tool
def run_monte_carlo_var(confidence_levels_csv: str = "0.95,0.99", horizon_days: int = 10) -> str:
    """Run Monte Carlo VaR/CVaR on the current portfolio.

    Args:
        confidence_levels_csv: comma-separated confidence levels, e.g. "0.95,0.99".
        horizon_days: risk horizon in trading days.
    """
    p = _require_portfolio()
    levels = tuple(float(x) for x in confidence_levels_csv.split(","))
    model = registry.create("var_model", "monte_carlo")
    result = model.compute(p, confidence_levels=levels, horizon_days=horizon_days)
    return json.dumps(
        {
            "model": result.model_name,
            "horizon_days": result.horizon_days,
            "portfolio_value": result.portfolio_value,
            "var_by_confidence": result.var_by_confidence,
            "cvar_by_confidence": result.cvar_by_confidence,
        },
        indent=2,
    )


@tool
def run_distress_model() -> str:
    """Run the logistic regression distress model on the current
    portfolio and return the highest-risk holdings plus the portfolio's
    total expected-distressed value."""
    p = _require_portfolio()
    model = registry.create("distress_model", "logistic_regression")
    result = model.predict(p)
    top10 = result.position_probabilities.head(10)[
        ["name", "sector", "market_value", "distress_probability"]
    ]
    return json.dumps(
        {
            "model": result.model_name,
            "portfolio_expected_distressed_value": result.portfolio_expected_distressed_value,
            "top_10_highest_risk_holdings": top10.to_dict(orient="records"),
        },
        indent=2,
        default=str,
    )


@tool
def run_risk_attribution(confidence_levels_csv: str = "0.95,0.99", horizon_days: int = 10) -> str:
    """Run component VaR risk attribution on the current portfolio,
    returning the top contributors to risk by position and by sector.
    Internally runs Monte Carlo VaR first to get the simulated P&L
    distribution to attribute from."""
    p = _require_portfolio()
    levels = tuple(float(x) for x in confidence_levels_csv.split(","))
    var_model = registry.create("var_model", "monte_carlo")
    var_result = var_model.compute(p, confidence_levels=levels, horizon_days=horizon_days)

    attribution_model = registry.create("attribution_model", "component_var")
    result = attribution_model.compute(p, var_result)

    return json.dumps(
        {
            "model": result.model_name,
            "top_5_position_contributors": result.by_position.head(5)[
                ["name", "sector", "component_var", "pct_of_var"]
            ].to_dict(orient="records"),
            "sector_contribution": result.by_sector.to_dict(orient="records"),
        },
        indent=2,
        default=str,
    )


ALL_TOOLS = [
    list_available_models,
    get_portfolio_summary,
    run_stress_scenario,
    run_monte_carlo_var,
    run_distress_model,
    run_risk_attribution,
]
