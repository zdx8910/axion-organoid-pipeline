"""Workflow A (Fig. 1): Axion spike CSV ingestion and schema normalization."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import pandas as pd

from meaorganoid._typing import CsvSource
from meaorganoid.errors import MEASchemaError

_ALIASES: Mapping[str, tuple[str, ...]] = {
    "time_s": ("Time (s)", "Time", "Timestamp", "Spike Time", "SpikeTime", "time_s"),
    "electrode": ("Electrode", "Channel", "Electrode Name", "Channel Label"),
    "well": ("Well", "Well Label", "Well ID", "WellName"),
}
_REQUIRED_COLUMNS = ("time_s", "electrode")


def _normalise_column_name(column: object) -> str:
    return str(column).strip().casefold()


def _source_name(source: CsvSource) -> str:
    if isinstance(source, str | Path):
        return str(source)
    return str(getattr(source, "name", "<buffer>"))


def resolve_columns(columns: Sequence[object], source: str | Path = "<buffer>") -> dict[str, str]:
    """Resolve Axion spike CSV column aliases to canonical column names.

    Parameters
    ----------
    columns
        Column names seen in the input CSV.
    source
        Input path or display name used in schema error messages.

    Returns
    -------
    dict[str, str]
        Mapping from canonical column name to the original input column name.

    Examples
    --------
    >>> resolve_columns(["Time (s)", "Electrode"])
    {'time_s': 'Time (s)', 'electrode': 'Electrode'}
    """
    seen = {_normalise_column_name(column): str(column) for column in columns}
    resolved: dict[str, str] = {}

    for canonical, aliases in _ALIASES.items():
        for alias in aliases:
            matched = seen.get(_normalise_column_name(alias))
            if matched is not None:
                resolved[canonical] = matched
                break

    missing = [column for column in _REQUIRED_COLUMNS if column not in resolved]
    if missing:
        raise MEASchemaError(
            f"{source}: missing required column(s) {missing}; saw columns {list(map(str, columns))}"
        )

    return resolved


def read_axion_spike_csv(source: CsvSource) -> pd.DataFrame:
    """Read an Axion spike CSV and return tidy canonical spike events.

    Parameters
    ----------
    source
        Path or text buffer containing an Axion spike CSV export. Supported aliases are documented
        in ``AGENTS.md`` and normalized to ``time_s``, ``electrode``, and optionally ``well``.

    Returns
    -------
    pandas.DataFrame
        Spike events with canonical columns first, followed by any non-conflicting input columns.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    source_label = _source_name(source)
    data = pd.read_csv(source)
    resolved = resolve_columns(list(data.columns), source=source_label)
    rename_map = {original: canonical for canonical, original in resolved.items()}
    tidy = data.rename(columns=rename_map).copy()

    ordered_columns = [
        column for column in ("time_s", "electrode", "well") if column in tidy.columns
    ]
    extra_columns = [column for column in tidy.columns if column not in ordered_columns]
    tidy = cast(pd.DataFrame, tidy.loc[:, ordered_columns + extra_columns].copy())
    tidy["time_s"] = pd.to_numeric(tidy["time_s"], errors="raise")
    tidy["electrode"] = tidy["electrode"].astype(str)
    if "well" in tidy.columns:
        tidy["well"] = tidy["well"].astype(str)
    return tidy
