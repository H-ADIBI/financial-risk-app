"""
A tiny plugin registry that makes the whole risk engine extensible.

The idea: every "kind of model" (a portfolio source, a stress scenario,
a VaR model, a distress model, an attribution method, a forecasting
model, ...) is a *category*. Concrete implementations register
themselves against a category with a short key, using the `@register`
decorator, at import time.

    @register("var_model", "monte_carlo")
    class MonteCarloVaR(VaRModel):
        ...

Every subpackage's __init__.py auto-imports every .py file sitting next
to it (see e.g. risk_engine/scenarios/__init__.py), which triggers those
decorators. The practical effect:

  - To ADD a new model: drop a new file in the right folder (e.g.
    risk_engine/var/historical_sim.py) implementing the category's base
    class and decorate it with @register(...). It shows up automatically
    in the Streamlit selectors and in the AI analyst's toolset -- no
    other file needs to change.
  - To REMOVE a model: delete (or rename) its file.
  - To MODIFY a model: edit its file; everything that looks it up by key
    keeps working.

This is exactly the seam you'd use to add, say, an ARIMAX-based interest
rate forecaster later: create risk_engine/forecasting/arimax.py,
implement ForecastModel, register it as ("forecast_model", "arimax"),
and it becomes selectable everywhere a forecast model is selectable
(including as an input to the rate-shock stress scenario).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Type

_REGISTRY: dict[str, dict[str, Type]] = defaultdict(dict)
_METADATA: dict[str, dict[str, dict]] = defaultdict(dict)


def register(category: str, key: str, **metadata):
    """Class decorator that registers a class under (category, key)."""

    def decorator(cls: Type) -> Type:
        if key in _REGISTRY[category]:
            raise ValueError(f"'{key}' is already registered under category '{category}'")
        _REGISTRY[category][key] = cls
        _METADATA[category][key] = metadata
        cls.registry_key = key
        return cls

    return decorator


def get(category: str, key: str) -> Type:
    try:
        return _REGISTRY[category][key]
    except KeyError as exc:
        available = list(_REGISTRY.get(category, {}).keys())
        raise KeyError(
            f"No implementation '{key}' registered under category '{category}'. "
            f"Available: {available}"
        ) from exc


def create(category: str, key: str, *args, **kwargs):
    """Instantiate a registered class in one call."""
    return get(category, key)(*args, **kwargs)


def list_keys(category: str) -> list[str]:
    return list(_REGISTRY.get(category, {}).keys())


def metadata(category: str, key: str) -> dict:
    return _METADATA.get(category, {}).get(key, {})


def all_categories() -> dict[str, list[str]]:
    return {cat: list(impls.keys()) for cat, impls in _REGISTRY.items()}
