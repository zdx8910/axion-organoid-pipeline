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


def _find_header_row(source: CsvSource) -> int:
    """Return the 0-based row index of the real column-header row."""
    time_aliases_lower = {_normalise_column_name(a) for a in _ALIASES["time_s"]}
    if isinstance(source, str | Path):
        with open(source, encoding="utf-8-sig", errors="replace") as fh:
            for idx, raw_line in enumerate(fh):
                if idx > 200:
                    break
                cells = [c.strip() for c in raw_line.rstrip("\r\n").split(",")]
                if any(_normalise_column_name(c) in time_aliases_lower for c in cells):
                    return idx
    return 0


def _is_axion_mixed_layout(source: CsvSource) -> bool:
    """Return True when the file uses the Axion NMT mixed-layout format."""
    try:
        if isinstance(source, str | Path):
            with open(source, encoding="utf-8-sig", errors="replace") as fh:
                lines = [fh.readline() for _ in range(2)]
        else:
            pos = source.tell()
            lines = [source.readline() for _ in range(2)]  # type: ignore[union-attr]
            source.seek(pos)  # type: ignore[union-attr]
        if len(lines) < 2:
            return False
        row0 = [c.strip() for c in lines[0].rstrip("\r\n").split(",")]
        row1 = [c.strip() for c in lines[1].rstrip("\r\n").split(",")]
        time_aliases_lower = {_normalise_column_name(a) for a in _ALIASES["time_s"]}
        col2_is_time_header = (
            len(row0) > 2 and _normalise_column_name(row0[2]) in time_aliases_lower
        )
        if not col2_is_time_header:
            return False
        try:
            float(row1[2])
            return True
        except (ValueError, IndexError):
            return False
    except OSError:
        return False


def _parse_axion_mixed_layout(source: CsvSource, source_label: str) -> pd.DataFrame:
    """Extract spike events from an Axion NMT mixed-layout CSV."""
    if isinstance(source, str | Path):
        with open(source, encoding="utf-8-sig", errors="replace") as fh:
            raw_lines = fh.readlines()
    else:
        pos = source.tell()  # type: ignore[union-attr]
        raw_lines = source.readlines()  # type: ignore[union-attr]
        source.seek(pos)  # type: ignore[union-attr]

    header_cells = [c.strip() for c in raw_lines[0].rstrip("\r\n").split(",")]
    col_names = header_cells[2:]

    records = []
    for line in raw_lines[1:]:
        cells = [c.strip() for c in line.rstrip("\r\n").split(",")]
        if len(cells) < len(col_names) + 2:
            continue
        spike_cells = cells[2: 2 + len(col_names)]
        try:
            float(spike_cells[0])
        except (ValueError, IndexError):
            continue
        records.append(spike_cells)

    if not records:
        raise MEASchemaError(f"{source_label}: no parseable spike rows found in mixed-layout CSV")

    df = pd.DataFrame(records, columns=col_names)
    resolved = resolve_columns(col_names, source=source_label)
    rename_map = {original: canonical for canonical, original in resolved.items()}
    df = df.rename(columns=rename_map)
    df["time_s"] = pd.to_numeric(df["time_s"], errors="coerce").astype("float64")
    df = cast(pd.DataFrame, df.dropna(subset=["time_s"]).copy())
    LOGGER.info("%s: extracted %d spike events from mixed-layout CSV", source_label, len(df))
    return df


def read_axion_spike_csv(source: CsvSource) -> pd.DataFrame:
    """Read an Axion spike CSV and return tidy canonical spike events.

    Parameters
    ----------
    source
        Path or text buffer containing an Axion spike CSV export.

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

    if _is_axion_mixed_layout(source):
        LOGGER.info(
            "%s: detected Axion mixed-layout CSV; extracting spike columns directly",
            source_label,
        )
        tidy = _parse_axion_mixed_layout(source, source_label)
    else:
        header_row = _find_header_row(source)
        if header_row > 0:
            LOGGER.info(
                "%s: skipping %d Axion metadata row(s) before column header",
                source_label,
                header_row,
            )
        data = pd.read_csv(
            source,
            skiprows=header_row,
            on_bad_lines="skip",
            encoding_errors="replace",
        )
        data.columns = [str(column).strip() for column in data.columns]
        resolved = resolve_columns(list(data.columns), source=source_label)
        rename_map = {original: canonical for canonical, original in resolved.items()}
        tidy = data.rename(columns=rename_map).copy()
        tidy["time_s"] = pd.to_numeric(tidy["time_s"], errors="coerce").astype("float64")
        tidy = cast(pd.DataFrame, tidy.dropna(subset=["time_s"]).copy())

    tidy["electrode"] = tidy["electrode"].fillna("").astype("string")
    if "well" in tidy.columns:
        tidy["well"] = tidy["well"].fillna("").astype("string")
    else:
        tidy["well"] = _infer_well_from_electrodes(tidy["electrode"], source_label)

    ordered_columns = list(canonical_columns())
    extra_columns = [column for column in tidy.columns if column not in ordered_columns]
    tidy = cast(pd.DataFrame, tidy.loc[:, ordered_columns + extra_columns].copy())
    return tidy
