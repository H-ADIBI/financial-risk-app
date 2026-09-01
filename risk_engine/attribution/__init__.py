"""Auto-discovery: drop a new attribution method file here decorated
with @register("attribution_model", "your_key") to add it as an option."""
import importlib
import pkgutil

for _finder, _module_name, _is_pkg in pkgutil.iter_modules(__path__):
    if _module_name != "base":
        importlib.import_module(f"{__name__}.{_module_name}")
