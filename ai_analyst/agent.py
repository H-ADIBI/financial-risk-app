"""
LangGraph agent wiring: a small ReAct-style graph (LLM node <-> tools
node) built with LangGraph's prebuilt helper, backed by Groq (free-tier
hosted open models) via langchain-groq.

Kept intentionally simple (a single reasoning/tool-calling loop) since
the interesting extensibility surface for this app is the risk_engine
registry, not the graph topology -- but this file is a normal LangGraph
graph, so it's straightforward to grow into a multi-node graph later
(e.g. a dedicated "planner" node, a "report writer" node, a
human-in-the-loop approval node before running expensive simulations).
"""
from __future__ import annotations

from functools import lru_cache

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from ai_analyst.prompts import SYSTEM_PROMPT
from ai_analyst.tools import ALL_TOOLS
from risk_engine.config import CONFIG


@lru_cache(maxsize=1)
def get_agent():
    if not CONFIG.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    llm = ChatGroq(model=CONFIG.groq_model, api_key=CONFIG.groq_api_key, temperature=0)
    return create_react_agent(llm, tools=ALL_TOOLS, prompt=SYSTEM_PROMPT)


def ask(question: str, chat_history: list[dict] | None = None) -> str:
    """Run one turn of the AI analyst. chat_history is a list of
    {"role": "user"|"assistant", "content": str} dicts from prior turns
    in the Streamlit session, so the agent has conversational context."""
    agent = get_agent()
    messages = list(chat_history or [])
    messages.append({"role": "user", "content": question})
    result = agent.invoke({"messages": messages})
    final_message = result["messages"][-1]
    return final_message.content
