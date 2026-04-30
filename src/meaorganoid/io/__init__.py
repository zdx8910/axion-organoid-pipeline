"""Workflow A (Fig. 1): Axion spike CSV ingestion and schema normalization."""

import logging
import re
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
_CANONICAL_COLUMNS = ("time_s", "electrode", "well")
_REQUIRED_COLUMNS = ("time_s", "electrode")
_AXION_ELECTRODE_RE = re.compile(r"^(?P<well>[A-Za-z][0-9]+)_[0-9]+$")
LOGGER = logging.getLogger(__name__)


def _normalise_column_name(column: object) -> str:
    return str(column).strip().casefold()


def _source_name(source: CsvSource) -> str:
    if isinstance(source, str | Path):
        return str(source)
    return str(getattr(source, "name", "<buffer>"))


def canonical_columns() -> tuple[str, str, str]:
    """Return the canonical column order for Workflow A spike events.

    Parameters
    ----------
    None
        This helper takes no parameters.

    Returns
    -------
    tuple[str, str, str]
        The canonical spike-event columns: ``time_s``, ``electrode``, and ``well``.

    Examples
    --------
    >>> canonical_columns()
    ('time_s', 'electrode', 'well')
    """
    return _CANONICAL_COLUMNS


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
    stripped_columns = [str(column).strip() for column in columns]
    seen = {_normalise_column_name(column): column for column in stripped_columns}
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
            f"{source}: missing required column(s) {missing}; columns seen: {stripped_columns}"
        )

    return resolved


def _infer_well_from_electrodes(electrodes: pd.Series, source: str) -> pd.Series:
    labels = electrodes.fillna("").astype("string")
    if labels.empty:
        return pd.Series("", index=electrodes.index, dtype="string")

    matches = labels.str.extract(_AXION_ELECTRODE_RE, expand=True)
    if bool(matches["well"].notna().all()):
        return cast(pd.Series, matches["well"].astype("string"))

    LOGGER.warning(
        "%s: could not infer well for every electrode label; leaving well as empty string",
        source,
    )
    return pd.Series("", index=electrodes.index, dtype="string")


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
    >>> from pathlib import Path
    >>> fixture = Path(__file__).parents[3] / "tests" / "fixtures" / "axion_minimal.csv"
    >>> read_axion_spike_csv(fixture).loc[:, list(canonical_columns())].head(1).to_dict("records")
    [{'time_s': 0.0, 'electrode': 'E1', 'well': ''}]
    """
    source_label = _source_name(source)
    data = pd.read_csv(source)
    data.columns = [str(column).strip() for column in data.columns]
    resolved = resolve_columns(list(data.columns), source=source_label)
    rename_map = {original: canonical for canonical, original in resolved.items()}
    tidy = data.rename(columns=rename_map).copy()

    tidy["time_s"] = pd.to_numeric(tidy["time_s"], errors="raise").astype("float64")
    tidy["electrode"] = tidy["electrode"].fillna("").astype("string")
    if "well" in tidy.columns:
        tidy["well"] = tidy["well"].fillna("").astype("string")
    else:
        tidy["well"] = _infer_well_from_electrodes(tidy["electrode"], source_label)

    ordered_columns = list(canonical_columns())
    extra_columns = [column for column in tidy.columns if column not in ordered_columns]
    tidy = cast(pd.DataFrame, tidy.loc[:, ordered_columns + extra_columns].copy())
    return tidy
