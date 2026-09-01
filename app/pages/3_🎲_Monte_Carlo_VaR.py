import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.ui_components.charts import pnl_histogram
from app.ui_components.session import page_header, require_portfolio_or_stop
from risk_engine import registry
from risk_engine.config import CONFIG

import risk_engine.var  # noqa: F401

page_header(
    "Monte Carlo VaR",
    "Correlated simulation-based Value-at-Risk and Conditional VaR (Expected Shortfall).",
    icon="🎲",
)

portfolio = require_portfolio_or_stop()

model_keys = registry.list_keys("var_model")
model_labels = {k: registry.get("var_model", k).display_name for k in model_keys}
selected_key = st.selectbox("VaR model", options=model_keys, format_func=lambda k: model_labels.get(k, k))
st.caption(registry.get("var_model", selected_key).description)

c1, c2, c3 = st.columns(3)
horizon = c1.number_input("Horizon (trading days)", min_value=1, max_value=252, value=CONFIG.mc_horizon_days)
num_sims = c2.number_input("Simulations", min_value=1000, max_value=100_000, value=CONFIG.mc_num_simulations, step=1000)
conf_input = c3.text_input("Confidence levels (comma-separated)", value="0.95,0.99")

if st.button("Run Monte Carlo VaR", type="primary"):
    confidence_levels = tuple(float(x.strip()) for x in conf_input.split(","))
    model = registry.create("var_model", selected_key)
    result = model.compute(
        portfolio, confidence_levels=confidence_levels, horizon_days=int(horizon), num_simulations=int(num_sims)
    )
    st.session_state["last_var_result"] = result

if "last_var_result" in st.session_state:
    result = st.session_state["last_var_result"]

    cols = st.columns(len(result.confidence_levels) * 2)
    i = 0
    for cl in result.confidence_levels:
        cols[i].metric(f"VaR ({cl:.0%})", f"${result.var_by_confidence[cl]:,.0f}")
        cols[i + 1].metric(f"CVaR ({cl:.0%})", f"${result.cvar_by_confidence[cl]:,.0f}")
        i += 2

    hist_df = pd.DataFrame({"pnl": result.simulated_pnl})
    thresholds = {f"VaR {cl:.0%}": -result.var_by_confidence[cl] for cl in result.confidence_levels}
    pnl_histogram(result.simulated_pnl, thresholds, "Simulated portfolio P&L distribution")
    st.caption(
        f"Histogram of {len(result.simulated_pnl):,} simulated {result.horizon_days}-day P&L outcomes, "
        "with the VaR cutoff(s) marked."
    )

    st.subheader("Distribution summary")
    st.dataframe(
        pd.DataFrame(hist_df["pnl"].describe()).T.style.format("{:,.0f}"),
        use_container_width=True,
    )
