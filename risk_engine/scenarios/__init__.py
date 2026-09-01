"""Auto-discovery: drop a new scenario file in this folder and decorate
its class with @register("scenario", "your_key") -- it will appear in
the Streamlit Stress Testing page and to the AI analyst automatically."""
import importlib
import pkgutil

for _finder, _module_name, _is_pkg in pkgutil.iter_modules(__path__):
    if _module_name not in ("base", "shocks"):
        importlib.import_module(f"{__name__}.{_module_name}")
