"""Auto-discovery: importing this package imports every sibling module,
which is what triggers each module's @register(...) decorators. Drop a
new source file in this folder (e.g. bloomberg_source.py) and it will be
picked up automatically -- no edits needed here."""
import importlib
import pkgutil

for _finder, _module_name, _is_pkg in pkgutil.iter_modules(__path__):
    if _module_name not in ("base",):
        importlib.import_module(f"{__name__}.{_module_name}")
