"""Auto-discovery for forecasting models. To add ARIMAX-based rate
forecasting: add risk_engine/forecasting/arimax.py implementing
ForecastModel and decorated with @register("forecast_model", "arimax")."""
import importlib
import pkgutil

for _finder, _module_name, _is_pkg in pkgutil.iter_modules(__path__):
    if _module_name != "base":
        importlib.import_module(f"{__name__}.{_module_name}")
