"""CSV-first analysis toolkit for Axion MEA recordings of brain organoids."""

from importlib.metadata import PackageNotFoundError, version

from meaorganoid.errors import MEAQCError, MEASchemaError, MEAValueError
from meaorganoid.io import read_axion_spike_csv, resolve_columns

try:
    __version__ = version("meaorganoid")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "MEAQCError",
    "MEASchemaError",
    "MEAValueError",
    "__version__",
    "read_axion_spike_csv",
    "resolve_columns",
]
