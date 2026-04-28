"""Shared type aliases for meaorganoid."""

from pathlib import Path
from typing import TextIO, TypeAlias

PathLike: TypeAlias = str | Path
CsvSource: TypeAlias = PathLike | TextIO
