import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.ui_components.charts import diverging_bar
from app.ui_components.session import page_header, require_portfolio_or_stop
from risk_engine import registry

import risk_engine.scenarios  # noqa: F401

page_header("Stress Testing", "OSFI-aligned macro stress scenarios applied to the current portfolio.", icon="⚡")

portfolio = require_portfolio_or_stop()

scenario_keys = registry.list_keys("scenario")
scenario_labels = {k: registry.get("scenario", k).display_name for k in scenario_keys}

selected_key = st.selectbox("Scenario", options=scenario_keys, format_func=lambda k: scenario_labels.get(k, k))
scenario_cls = registry.get("scenario", selected_key)
st.caption(scenario_cls.description)

with st.expander("Adjust shock magnitudes (optional)"):
    overrides = {}
    defaults = getattr(scenario_cls, "defaults", None) or {
        k: getattr(scenario_cls, k) for k in ("default_bps", "default_pct") if hasattr(scenario_cls, k)
    }
    if "rate_shock_bps" in defaults or hasattr(scenario_cls, "default_bps") and "rate" in selected_key:
        pass
    # Generic sliders keyed by whatever this scenario's default shock params are
    if selected_key == "rate_shock_up":
        overrides["rate_shock_bps"] = st.slider("Rate shock (bps)", -300, 300, scenario_cls.default_bps)
    elif selected_key == "credit_spread_widening":
        overrides["credit_spread_shock_bps"] = st.slider("Credit spread shock (bps)", 0, 500, scenario_cls.default_bps)
    elif selected_key == "equity_drawdown":
        overrides["equity_shock_pct"] = st.slider("Equity shock (%)", -80, 20, int(scenario_cls.default_pct * 100)) / 100
    elif selected_key == "fx_shock":
        overrides["fx_shock_pct"] = st.slider("FX shock (%)", -50, 50, int(scenario_cls.default_pct * 100)) / 100
    elif selected_key == "severe_adverse":
        d = scenario_cls.defaults
        overrides["rate_shock_bps"] = st.slider("Rate shock (bps)", -300, 300, d["rate_shock_bps"])
        overrides["credit_spread_shock_bps"] = st.slider("Credit spread shock (bps)", 0, 500, d["credit_spread_shock_bps"])
        overrides["equity_shock_pct"] = st.slider("Equity shock (%)", -80, 20, int(d["equity_shock_pct"] * 100)) / 100
        overrides["fx_shock_pct"] = st.slider("FX shock (%)", -50, 50, int(d["fx_shock_pct"] * 100)) / 100

if st.button("Run scenario", type="primary"):
    scenario = registry.create("scenario", selected_key)
    result = scenario.apply(portfolio, shock_inputs=overrides)

    st.session_state["last_scenario_result"] = result

if "last_scenario_result" in st.session_state:
    result = st.session_state["last_scenario_result"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Base Value", f"${result.base_value:,.0f}")
    c2.metric("Shocked Value", f"${result.shocked_value:,.0f}")
    c3.metric("Total P&L", f"${result.total_pnl:,.0f}", delta=f"{result.total_pnl_pct:.2%}")

    by_sector = result.position_pnl.groupby("sector")["pnl"].sum().sort_values()
    diverging_bar(by_sector, "Impact by sector ($ P&L)")

    st.subheader("Largest position-level impacts")
    st.dataframe(
        result.position_pnl.sort_values("pnl").head(15)[
            ["name", "asset_class", "sector", "base_value", "pnl", "pct_change"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Full position-level detail"):
        st.dataframe(result.position_pnl, use_container_width=True, hide_index=True)
