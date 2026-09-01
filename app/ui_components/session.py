"""
Shared session-state helpers so every page reads/writes the loaded
Portfolio the same way, and a shared page-config/header so the app
looks consistent across pages.
"""
from __future__ import annotations

import streamlit as st

import risk_engine.data  # noqa: F401 -- triggers auto-discovery of sources
from risk_engine.data.models import Portfolio
from risk_engine.registry import create


def get_portfolio() -> Portfolio | None:
    return st.session_state.get("portfolio")


def set_portfolio(portfolio: Portfolio) -> None:
    st.session_state["portfolio"] = portfolio


def ensure_default_portfolio() -> Portfolio:
    """Loads a random sample portfolio on first visit so every page has
    something to show immediately."""
    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = create("portfolio_source", "random").load()
    return st.session_state["portfolio"]


def page_header(title: str, subtitle: str = "", icon: str = "📊"):
    st.set_page_config(page_title=f"{title} · ADB Stress Testing Assistant", page_icon=icon, layout="wide")
    palette = {
        "app": "#f7f4ee",
        "surface": "#fffdfa",
        "soft": "#f0ede6",
        "border": "#d9d4ca",
        "ink": "#242321",
        "muted": "#6d6a63",
        "accent": "#d97757",
    }
    with st.sidebar:
        st.markdown("## ADB Stress Testing Assistant")
        st.caption("Portfolio risk intelligence")
        st.divider()
        st.text_area(
            "Notes",
            key="user_notes",
            placeholder="Write a note about your analysis...",
            height=140,
        )
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: light; }}
        .stApp {{ background: {palette['app']}; color: {palette['ink']}; }}
        .stApp::before {{ content: ""; position: fixed; inset: 0; pointer-events: none; z-index: -1;
            background: radial-gradient(circle at 12% 8%, rgba(217,119,87,0.11), transparent 28%),
                        radial-gradient(circle at 88% 92%, rgba(102,126,139,0.10), transparent 30%); }}
        .stApp, .stApp p, .stApp label, .stApp [data-testid="stMarkdownContainer"] {{ color: {palette['ink']}; }}
        .stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div {{
            background: {palette['soft']}; color: {palette['ink']}; border-color: {palette['border']}; }}
        .risk-brand {{ color: {palette['accent']}; font-size: 0.78rem; font-weight: 700;
            letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.55rem; }}
        .risk-topnav {{ display: flex; justify-content: flex-end; gap: 1.25rem; margin: 0.1rem 0 1rem; }}
        .risk-topnav a {{ color: {palette['muted']}; font-size: 0.9rem; text-decoration: none; }}
        .risk-topnav a:hover {{ color: {palette['accent']}; text-decoration: underline; }}
        section[data-testid="stSidebar"] li:has(a[href$="/About_Me"]),
        section[data-testid="stSidebar"] li:has(a[href$="/Help_and_Process"]),
        section[data-testid="stSidebar"] li:has(a[href$="/"]) {{ display: none; }}
        /* -- Header -- */
        .risk-header {{
            padding-bottom: 0.4rem; margin-bottom: 0.15rem;
            border-bottom: 2px solid {palette['accent']};
            display: flex; align-items: center; gap: 0.55rem;
        }}
        .risk-subtitle {{color: {palette['muted']}; font-size: 0.95rem; margin-bottom: 1.1rem;}}

        /* -- Metric cards -- */
        div[data-testid="stMetric"] {{
            background: {palette['surface']};
            border: 1px solid {palette['border']};
            border-radius: 10px;
            padding: 0.9rem 1.1rem 0.75rem 1.1rem;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }}
        div[data-testid="stMetricValue"] {{font-size: 1.55rem; color: {palette['ink']};}}
        div[data-testid="stMetricLabel"] {{color: {palette['muted']};}}

        /* -- Section headings -- */
        h3 {{color: {palette['ink']};}}

        /* -- Buttons -- */
        div[data-testid="stButton"] button {{
            border-radius: 8px;
            font-weight: 500;
        }}
        div[data-testid="stButton"] button[kind="primary"] {{
            background-color: #b85d43;
            border-color: #b85d43;
        }}
        div[data-testid="stButton"] button[kind="primary"]:hover {{
            background-color: #d97757;
            border-color: #d97757;
        }}

        /* -- Containers used as cards -- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 12px !important;
        }}

        /* -- Dataframes / tables -- */
        div[data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
        }}

        /* -- Tabs -- */
        button[data-testid="stTab"] {{font-weight: 500;}}

        /* -- Sidebar -- */
        section[data-testid="stSidebar"] {{
            background: {palette['soft']};
            border-right: 1px solid {palette['border']};
        }}

        /* -- Chat -- */
        div[data-testid="stChatMessage"] {{
            border-radius: 12px;
            border: 1px solid {palette['border']};
            background: {palette['surface']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<nav class='risk-topnav'><a href='/'>Home</a><a href='/About_Me'>About me</a><a href='/Help_and_Process'>Help &amp; process</a></nav>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='risk-brand'>ADB · Risk intelligence workspace</div>", unsafe_allow_html=True)
    st.markdown(f"<h2 class='risk-header'>{icon} {title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='risk-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def require_portfolio_or_stop():
    portfolio = ensure_default_portfolio()
    if portfolio is None or len(portfolio.positions) == 0:
        st.warning("No portfolio loaded. Go to the Portfolio page to load or generate one.")
        st.stop()
    return portfolio
