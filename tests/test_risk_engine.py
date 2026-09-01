"""
Smoke tests: not exhaustive, but enough to catch a broken import, a
registry wiring mistake, or a math error that produces NaN/garbage
whenever the risk engine changes. Run with `pytest`.
"""
import numpy as np
import pytest

import risk_engine.attribution  # noqa: F401
import risk_engine.credit  # noqa: F401
import risk_engine.data  # noqa: F401
import risk_engine.forecasting  # noqa: F401
import risk_engine.scenarios  # noqa: F401
import risk_engine.var  # noqa: F401
from risk_engine import registry
from risk_engine.data.models import Portfolio, Position


@pytest.fixture
def sample_portfolio() -> Portfolio:
    return registry.create("portfolio_source", "random").load(num_positions=15, seed=1)


def test_registry_has_expected_categories():
    categories = registry.all_categories()
    for expected in ["portfolio_source", "scenario", "var_model", "distress_model", "attribution_model", "forecast_model"]:
        assert expected in categories
        assert len(categories[expected]) >= 1


def test_random_portfolio_source_produces_valid_portfolio(sample_portfolio):
    assert len(sample_portfolio.positions) == 15
    assert sample_portfolio.total_market_value > 0
    weights = [p.weight for p in sample_portfolio.positions]
    assert abs(sum(weights) - 1.0) < 1e-6


def test_all_scenarios_run_without_error(sample_portfolio):
    for key in registry.list_keys("scenario"):
        scenario = registry.create("scenario", key)
        result = scenario.apply(sample_portfolio)
        assert np.isfinite(result.base_value)
        assert np.isfinite(result.shocked_value)
        assert len(result.position_pnl) == len(sample_portfolio.positions)


def test_monte_carlo_var_is_positive_and_ordered(sample_portfolio):
    model = registry.create("var_model", "monte_carlo")
    result = model.compute(sample_portfolio, confidence_levels=(0.95, 0.99), horizon_days=10, num_simulations=2000)
    assert result.var_by_confidence[0.95] > 0
    assert result.var_by_confidence[0.99] >= result.var_by_confidence[0.95]
    assert result.cvar_by_confidence[0.99] >= result.var_by_confidence[0.99]


def test_distress_model_predicts_probabilities_in_range(sample_portfolio):
    model = registry.create("distress_model", "logistic_regression")
    result = model.predict(sample_portfolio)
    probs = result.position_probabilities["distress_probability"]
    assert (probs >= 0).all() and (probs <= 1).all()
    assert result.portfolio_expected_distressed_value >= 0


def test_attribution_sums_close_to_total_var(sample_portfolio):
    var_model = registry.create("var_model", "monte_carlo")
    var_result = var_model.compute(sample_portfolio, confidence_levels=(0.95,), horizon_days=10, num_simulations=5000)

    attribution_model = registry.create("attribution_model", "component_var")
    result = attribution_model.compute(sample_portfolio, var_result)

    total_component = result.by_position["component_var"].sum()
    assert total_component > 0
    assert abs(result.by_position["pct_of_var"].sum() - 1.0) < 1e-6


def test_csv_portfolio_source_roundtrip(tmp_path, sample_portfolio):
    csv_path = tmp_path / "portfolio.csv"
    sample_portfolio.to_dataframe().to_csv(csv_path, index=False)

    loaded = registry.create("portfolio_source", "csv").load(str(csv_path), name="From CSV")
    assert len(loaded.positions) == len(sample_portfolio.positions)
    assert abs(loaded.total_market_value - sample_portfolio.total_market_value) < 1.0


def test_naive_forecast_model_runs():
    import pandas as pd

    model = registry.create("forecast_model", "naive_drift")
    history = pd.Series(np.linspace(2.0, 3.0, 24), name="10Y_rate")
    result = model.forecast(history, horizon_periods=6)
    assert len(result.forecast) == 6
    assert np.isfinite(result.implied_shock())
