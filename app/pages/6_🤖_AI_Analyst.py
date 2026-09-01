import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.ui_components.session import page_header, require_portfolio_or_stop

page_header("AI Analyst", "Ask questions in plain English. The agent runs the risk models above for you.", icon="🤖")

portfolio = require_portfolio_or_stop()

if not st.session_state.get("_ai_analyst_import_ok", False):
    try:
        from ai_analyst.agent import ask
        from ai_analyst.tools import set_active_portfolio

        st.session_state["_ai_analyst_import_ok"] = True
    except Exception as exc:
        st.error(
            "The AI analyst couldn't be initialized. Make sure dependencies are installed "
            f"and GROQ_API_KEY is set in your .env file.\n\nDetails: {exc}"
        )
        st.stop()
else:
    from ai_analyst.agent import ask
    from ai_analyst.tools import set_active_portfolio

set_active_portfolio(portfolio)

st.caption(
    f"Currently analyzing: **{portfolio.name}** (${portfolio.total_market_value:,.0f}, "
    f"{len(portfolio.positions)} positions). Try: \"How risky is this portfolio under a severe "
    "recession scenario?\" or \"Which sectors are driving our VaR?\""
)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask the AI risk analyst...")
if question:
    st.session_state["chat_history"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Running risk models..."):
            try:
                answer = ask(question, chat_history=st.session_state["chat_history"][:-1])
            except Exception as exc:
                answer = f"Something went wrong: {exc}"
        st.markdown(answer)

    st.session_state["chat_history"].append({"role": "assistant", "content": answer})
