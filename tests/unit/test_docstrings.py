import importlib
import inspect

MODULES = [
    "meaorganoid.io",
    "meaorganoid.metrics",
    "meaorganoid.bursts",
    "meaorganoid.compare",
    "meaorganoid.qc",
    "meaorganoid.plot.raster",
    "meaorganoid.plot.spatial",
    "meaorganoid.plot.condition",
    "meaorganoid.connectivity",
]


def test_public_functions_have_numpy_docstring_sections() -> None:
    missing: list[str] = []
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or function.__module__ != module.__name__:
                continue
            doc = inspect.getdoc(function) or ""
            has_parameters = bool(inspect.signature(function).parameters)
            if "Returns" not in doc or (has_parameters and "Parameters" not in doc):
                missing.append(f"{module_name}.{name}")

    assert missing == []
