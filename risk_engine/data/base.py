"""Interface for anything that can produce a Portfolio. See registry.py
for how implementations plug into the app."""
from __future__ import annotations

from abc import ABC, abstractmethod

from risk_engine.data.models import Portfolio


class PortfolioSource(ABC):
    display_name: str = "Unnamed source"

    @abstractmethod
    def load(self, **kwargs) -> Portfolio:
        raise NotImplementedError
