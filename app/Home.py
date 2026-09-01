import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.ui_components.session import ensure_default_portfolio, page_header
from risk_engine import registry

import risk_engine.data  # noqa: F401
import risk_engine.scenarios  # noqa: F401
import risk_engine.var  # noqa: F401
import risk_engine.credit  # noqa: F401
import risk_engine.attribution  # noqa: F401
import risk_engine.forecasting  # noqa: F401

page_header(
    "ADB Stress Testing Assistant",
    "AI-enabled portfolio stress testing: OSFI-aligned scenarios, Monte Carlo VaR, "
    "issuer distress modeling, risk attribution, and an AI risk analyst.",
    icon="🏠",
)

portfolio = ensure_default_portfolio()

col1, col2, col3 = st.columns(3)
col1.metric("Portfolio", portfolio.name)
col2.metric("Total Market Value", f"${portfolio.total_market_value:,.0f}")
col3.metric("Positions", len(portfolio.positions))

st.write("")

modules = [
    ("💼", "Portfolio", "View the loaded book, generate a new random sample, or upload your own CSV."),
    ("⚡", "Stress Testing", "Run OSFI-aligned macro shock scenarios (rates, credit spreads, equities, FX)."),
    ("🎲", "Monte Carlo VaR", "Correlated simulation-based VaR and CVaR (Expected Shortfall)."),
    ("⚠️", "Distress Model", "Logistic-regression issuer distress probabilities."),
    ("🧩", "Risk Attribution", "Component VaR broken down by position, sector, and asset class."),
    ("🤖", "AI Analyst", "Ask questions in plain English; the agent runs the models above for you."),
]
st.subheader("What's in this app")
cols = st.columns(3)
for i, (icon, name, desc) in enumerate(modules):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"**{icon} {name}**")
            st.caption(desc)

st.write("")

with st.container(border=True):
    st.subheader("Registered models")
    st.caption(
        "Everything below is auto-discovered from the risk_engine package. Adding a new model "
        "(a new scenario, a new VaR method, an ARIMAX-based forecaster, etc.) makes it appear "
        "here automatically — see risk_engine/registry.py."
    )
    categories = registry.all_categories()
    cols = st.columns(len(categories)) if categories else []
    for col, (category, keys) in zip(cols, categories.items()):
        with col:
            st.markdown(f"**{category}**")
            for key in keys:
                meta = registry.metadata(category, key)
                st.caption(f"`{key}`" + (f" — {meta.get('description')}" if meta.get("description") else ""))
