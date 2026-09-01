import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.ui_components.charts import magnitude_bar
from app.ui_components.session import page_header, require_portfolio_or_stop, set_portfolio
from risk_engine import registry

import risk_engine.data  # noqa: F401

page_header("Portfolio", "Load, generate, or upload the portfolio every other page analyzes.", icon="💼")

source_keys = registry.list_keys("portfolio_source")
source_labels = {k: registry.get("portfolio_source", k).display_name for k in source_keys}

selected_key = st.selectbox(
    "Portfolio source",
    options=source_keys,
    format_func=lambda k: source_labels.get(k, k),
)

if selected_key == "random":
    c1, c2, c3 = st.columns(3)
    num_positions = c1.number_input("Number of positions", min_value=5, max_value=200, value=25)
    total_value = c2.number_input("Total portfolio value ($)", min_value=1_000_000, value=100_000_000, step=1_000_000)
    seed = c3.number_input("Random seed", min_value=0, value=42)
    if st.button("Generate portfolio", type="primary"):
        source = registry.create("portfolio_source", "random")
        portfolio = source.load(num_positions=int(num_positions), total_value=float(total_value), seed=int(seed))
        set_portfolio(portfolio)
        st.success(f"Generated a new {num_positions}-position portfolio.")
        st.rerun()

elif selected_key == "csv":
    st.caption(
        "Required columns: name, asset_class, sector, market_value. "
        "Optional: position_id, expected_return, volatility, duration, credit_spread_dur, "
        "equity_beta, fx_sensitivity, leverage_ratio, interest_coverage, current_ratio, profit_margin."
    )
    uploaded = st.file_uploader("Upload portfolio CSV", type=["csv"])
    if uploaded is not None and st.button("Load uploaded portfolio", type="primary"):
        try:
            source = registry.create("portfolio_source", "csv")
            portfolio = source.load(uploaded, name=uploaded.name)
            set_portfolio(portfolio)
            st.success(f"Loaded {len(portfolio.positions)} positions from {uploaded.name}.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not load CSV: {exc}")

st.divider()

portfolio = require_portfolio_or_stop()

st.subheader(f"Current portfolio: {portfolio.name}")
c1, c2 = st.columns(2)
c1.metric("Total Market Value", f"${portfolio.total_market_value:,.0f}")
c2.metric("Positions", len(portfolio.positions))

tab1, tab2, tab3 = st.tabs(["Positions", "Sector Exposure", "Asset Class Exposure"])
with tab1:
    st.dataframe(portfolio.to_dataframe(), use_container_width=True, hide_index=True)
with tab2:
    magnitude_bar(portfolio.sector_exposure(), "Market value by sector")
with tab3:
    magnitude_bar(portfolio.asset_class_exposure(), "Market value by asset class")
