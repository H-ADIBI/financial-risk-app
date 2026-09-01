import streamlit as st

from app.ui_components.session import page_header

page_header(
    "About ADB",
    "A focused workspace for turning portfolio risk questions into clear, inspectable analysis.",
    icon="👤",
)

with st.container(border=True):
    st.subheader("Built with a risk-first mindset")
    st.write(
        "ADB Stress Testing Assistant brings portfolio data, scenario analysis, statistical risk models, "
        "and an AI analyst into one practical workspace. The goal is to make each result easier to explore, "
        "question, and explain."
    )
    st.write(
        "The interface is intentionally calm and information-dense: the portfolio is the shared source of truth, "
        "the model registry keeps capabilities discoverable, and each dashboard exposes the assumptions behind its output."
    )

left, right = st.columns(2)
with left:
    st.markdown("**What matters here**")
    st.markdown("- Transparent assumptions")
    st.markdown("- Reusable risk-engine components")
    st.markdown("- OSFI-aligned stress scenarios")
with right:
    st.markdown("**The current toolkit**")
    st.markdown("- Portfolio and exposure analysis")
    st.markdown("- Monte Carlo VaR and CVaR")
    st.markdown("- Distress modeling and risk attribution")

st.info("The Help & Process page explains how a request moves through the application from input to insight.")
