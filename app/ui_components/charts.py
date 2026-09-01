"""Shared Plotly chart helpers so every dashboard uses one consistent,
validated color system instead of ad-hoc st.bar_chart defaults.

Color follows the job the data is doing (see dataviz skill):
- a single series of magnitudes by category (exposure, VaR contribution,
  distress probability) gets one hue -- color would just re-encode what
  the bar length already shows.
- gain/loss by category is polarity, so it gets the diverging blue/red pair.
- VaR/CVaR thresholds are a risk state, so they get the reserved status
  color plus a text label, never color alone.
"""
from __future__ import annotations

from typing import Mapping

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BLUE = "#2a78d6"
RED = "#e34948"
CRITICAL = "#d03b3b"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
MUTED = "#898781"
INK = "#1A1A1A"

_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", color=INK, size=13),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(bgcolor="white", bordercolor=GRID, font_size=13),
    title_font=dict(size=15, color=INK),
)

_CONFIG = {"displayModeBar": False}


def _style_axes(fig: go.Figure) -> None:
    dark_mode = st.session_state.get("dark_mode", False)
    axis = "#aaa59b" if dark_mode else AXIS
    muted = "#c5c0b7" if dark_mode else MUTED
    fig.update_xaxes(showgrid=True, gridcolor="#55534d" if dark_mode else GRID, zeroline=True, zerolinecolor=axis, tickfont=dict(color=muted))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=muted))


def _layout() -> dict:
    dark_mode = st.session_state.get("dark_mode", False)
    ink = "#f4f0e8" if dark_mode else INK
    return {**_LAYOUT, "font": {**_LAYOUT["font"], "color": ink}, "title_font": {"size": 15, "color": ink}}


def magnitude_bar(
    series: pd.Series,
    title: str,
    currency: bool = True,
    percent: bool = False,
    height: int = 360,
) -> None:
    """Horizontal bar chart for a single series of magnitudes by category."""
    ordered = series.sort_values()
    prefix = "$" if currency and not percent else ""
    hover_fmt = ".2%" if percent else ",.0f"
    fig = go.Figure(
        go.Bar(
            x=ordered.values,
            y=ordered.index.astype(str),
            orientation="h",
            marker_color=BLUE,
            hovertemplate=f"%{{y}}: {prefix}%{{x:{hover_fmt}}}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=height, showlegend=False, **_layout())
    _style_axes(fig)
    fig.update_xaxes(tickprefix=prefix, tickformat=".0%" if percent else ",.0f")
    st.plotly_chart(fig, use_container_width=True, config=_CONFIG)


def diverging_bar(
    series: pd.Series,
    title: str,
    currency: bool = True,
    height: int = 360,
) -> None:
    """Horizontal bar chart for a signed quantity by category -- blue for
    the positive side, red for the negative side, split at a zero baseline."""
    ordered = series.sort_values()
    prefix = "$" if currency else ""
    colors = [BLUE if v >= 0 else RED for v in ordered.values]
    fig = go.Figure(
        go.Bar(
            x=ordered.values,
            y=ordered.index.astype(str),
            orientation="h",
            marker_color=colors,
            hovertemplate=f"%{{y}}: {prefix}%{{x:,.0f}}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=height, showlegend=False, **_layout())
    _style_axes(fig)
    fig.update_xaxes(tickprefix=prefix, tickformat=",.0f")
    fig.add_vline(x=0, line_color=AXIS, line_width=1)
    st.plotly_chart(fig, use_container_width=True, config=_CONFIG)


def pnl_histogram(
    values,
    thresholds: Mapping[str, float],
    title: str,
    height: int = 380,
) -> None:
    """Simulated P&L distribution with VaR/CVaR cutoffs marked as dashed
    reference lines in the reserved risk (status) color, each labeled --
    never a threshold implied by color alone."""
    fig = go.Figure(
        go.Histogram(
            x=values,
            nbinsx=60,
            marker_color=BLUE,
            hovertemplate="P&L: $%{x:,.0f}<br>Count: %{y}<extra></extra>",
        )
    )
    for label, x in thresholds.items():
        fig.add_vline(
            x=x,
            line_color=CRITICAL,
            line_width=2,
            line_dash="dash",
            annotation_text=label,
            annotation_position="top",
            annotation_font_color=CRITICAL,
        )
    fig.update_layout(title=title, height=height, showlegend=False, **_layout())
    _style_axes(fig)
    fig.update_xaxes(title_text="Simulated P&L ($)", tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(title_text="Frequency")
    st.plotly_chart(fig, use_container_width=True, config=_CONFIG)
