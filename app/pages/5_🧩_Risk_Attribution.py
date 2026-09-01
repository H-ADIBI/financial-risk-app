import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.ui_components.charts import magnitude_bar
from app.ui_components.session import page_header, require_portfolio_or_stop
from risk_engine import registry
from risk_engine.config import CONFIG

import risk_engine.attribution  # noqa: F401
import risk_engine.var  # noqa: F401

page_header("Risk Attribution", "Decompose portfolio VaR by position, sector, and asset class.", icon="🧩")

portfolio = require_portfolio_or_stop()

c1, c2 = st.columns(2)
horizon = c1.number_input("Horizon (trading days)", min_value=1, max_value=252, value=CONFIG.mc_horizon_days)
conf_input = c2.text_input("Confidence levels (comma-separated)", value="0.95,0.99")

if st.button("Run risk attribution", type="primary"):
    confidence_levels = tuple(float(x.strip()) for x in conf_input.split(","))
    var_model = registry.create("var_model", "monte_carlo")
    var_result = var_model.compute(portfolio, confidence_levels=confidence_levels, horizon_days=int(horizon))

    attribution_model = registry.create("attribution_model", "component_var")
    result = attribution_model.compute(portfolio, var_result)
    st.session_state["last_attribution_result"] = result

if "last_attribution_result" in st.session_state:
    result = st.session_state["last_attribution_result"]

    magnitude_bar(result.by_sector.set_index("sector")["component_var"], "Contribution by sector")
    magnitude_bar(result.by_asset_class.set_index("asset_class")["component_var"], "Contribution by asset class")

    st.subheader("Top risk contributors (positions)")
    st.dataframe(
        result.by_position.head(15).style.format({"component_var": "${:,.0f}", "pct_of_var": "{:.2%}"}),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Full position-level attribution"):
        st.dataframe(result.by_position, use_container_width=True, hide_index=True)
