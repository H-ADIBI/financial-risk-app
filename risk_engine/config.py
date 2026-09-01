"""
Central configuration for the risk engine and AI analyst.

Keeping all tunables in one place makes it easy to extend later
(e.g. swap the random seed, add new sectors, point at a real market
data feed) without hunting through every module.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


SECTORS = [
    "Financials",
    "Energy",
    "Technology",
    "Industrials",
    "Consumer Discretionary",
    "Utilities",
    "Materials",
    "Government/Sovereign",
]

ASSET_CLASSES = ["Equity", "Corporate Bond", "Government Bond", "FX"]


@dataclass(frozen=True)
class AppConfig:
    # Portfolio generation
    default_num_positions: int = 25
    default_portfolio_value: float = 100_000_000.0  # $100mm book
    random_seed: int = 42

    # Monte Carlo VaR
    mc_num_simulations: int = 10_000
    mc_horizon_days: int = 10
    mc_confidence_levels: tuple = (0.95, 0.99)

    # AI analyst (Groq)
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    )


CONFIG = AppConfig()
