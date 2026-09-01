"""Auto-discovery: drop a new VaR model file here (e.g. historical_sim.py
or filtered_historical.py) decorated with @register("var_model", "your_key")
and it appears in the Monte Carlo VaR page and to the AI analyst."""
import importlib
import pkgutil

for _finder, _module_name, _is_pkg in pkgutil.iter_modules(__path__):
    if _module_name != "base":
        importlib.import_module(f"{__name__}.{_module_name}")
