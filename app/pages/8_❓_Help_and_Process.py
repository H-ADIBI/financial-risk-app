from pathlib import Path

import streamlit as st

from app.ui_components.session import page_header

page_header(
    "Help & Process",
    "How the application turns a portfolio and a question into risk insight.",
    icon="❓",
)

st.subheader("Application structure")
st.caption("A simple view of how data becomes risk insight.")
st.graphviz_chart(
    """
    digraph {
      graph [bgcolor=transparent, rankdir=LR, nodesep=0.25, ranksep=0.5, pad=0.1]
      node [shape=box, style="rounded,filled", fontname="Helvetica", color="#d97757", fillcolor="#fff8f1", fontcolor="#242321", margin="0.16,0.10", fontsize=10]
      edge [color="#8d8178", arrowsize=0.7, penwidth=1.1]

      input [label="1. INPUT\nCSV or sample portfolio\n\nOutput: portfolio data", fillcolor="#f0e7dd"]
      validate [label="2. VALIDATE\nCheck columns and values\n\nOutput: clean portfolio"]
      choose [label="3. CHOOSE\nSelect dashboard and model\n\nOutput: model parameters"]
      analyze [label="4. ANALYZE\nStress, VaR, distress,\nor attribution calculations\n\nOutput: risk results"]
      present [label="5. PRESENT\nBuild metrics, charts,\nand detailed tables\n\nOutput: dashboard insight", fillcolor="#e8f0ed"]
      review [label="6. REVIEW\nUser compares results\nor asks the AI Analyst", fillcolor="#e8f0ed"]

      input -> validate -> choose -> analyze -> present -> review
    }
    """,
    use_container_width=True,
)

st.markdown(Path(__file__).resolve().parents[2].joinpath("docs", "APP_PROCESS.md").read_text())
