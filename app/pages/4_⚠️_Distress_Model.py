import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.ui_components.charts import diverging_bar, magnitude_bar
from app.ui_components.session import page_header, require_portfolio_or_stop
from risk_engine import registry

import risk_engine.credit  # noqa: F401

page_header("Distress Model", "Logistic-regression-based issuer distress probability per holding.", icon="⚠️")

portfolio = require_portfolio_or_stop()

model_keys = registry.list_keys("distress_model")
model_labels = {k: registry.get("distress_model", k).display_name for k in model_keys}
selected_key = st.selectbox("Distress model", options=model_keys, format_func=lambda k: model_labels.get(k, k))
st.caption(registry.get("distress_model", selected_key).description)

if st.button("Run distress model", type="primary"):
    model = registry.create("distress_model", selected_key)
    result = model.predict(portfolio)
    st.session_state["last_distress_result"] = result
    if hasattr(model, "coefficients"):
        st.session_state["last_distress_coefs"] = model.coefficients()

if "last_distress_result" in st.session_state:
    result = st.session_state["last_distress_result"]

    c1, c2 = st.columns(2)
    c1.metric("Portfolio expected distressed value", f"${result.portfolio_expected_distressed_value:,.0f}")
    c2.metric(
        "% of portfolio",
        f"{result.portfolio_expected_distressed_value / portfolio.total_market_value:.2%}",
    )

    st.subheader("Highest-risk holdings")
    st.dataframe(
        result.position_probabilities.head(15).style.format({"distress_probability": "{:.2%}", "market_value": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

    by_sector = (
        result.position_probabilities.groupby("sector")["distress_probability"].mean().sort_values(ascending=False)
    )
    magnitude_bar(by_sector, "Distress probability by sector", currency=False, percent=True)

    if "last_distress_coefs" in st.session_state:
        with st.expander("Model coefficients (standardized)"):
            st.caption("Positive = increases distress probability; negative = decreases it.")
            diverging_bar(st.session_state["last_distress_coefs"], "Standardized coefficients", currency=False)
