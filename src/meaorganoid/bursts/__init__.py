"""Workflow B (Fig. 2): ISI-based burst detection."""

from collections.abc import Iterable
from typing import Any, Literal

import pandas as pd

from meaorganoid.bursts.logisi import detect_bursts_logisi
from meaorganoid.bursts.maxinterval import detect_bursts_maxinterval
from meaorganoid.errors import MEAValueError

__all__ = ["detect_bursts", "detect_bursts_logisi", "detect_bursts_maxinterval"]


def _empty_grouped_bursts(group_by: Iterable[str]) -> pd.DataFrame:
    group_columns = list(group_by)
    return pd.DataFrame(
        {
            **{column: pd.Series(dtype="object") for column in group_columns},
            "burst_index": pd.Series(dtype="int64"),
            "start_s": pd.Series(dtype="float64"),
            "end_s": pd.Series(dtype="float64"),
            "duration_s": pd.Series(dtype="float64"),
            "n_spikes": pd.Series(dtype="int64"),
            "mean_isi_s": pd.Series(dtype="float64"),
            "intra_burst_rate_hz": pd.Series(dtype="float64"),
        }
    )


def detect_bursts(
    events: pd.DataFrame,
    *,
    method: Literal["maxinterval", "logisi"] = "maxinterval",
    group_by: Iterable[str] = ("well", "electrode"),
    **kwargs: Any,
) -> pd.DataFrame:
    """Detect bursts in canonical Workflow A events grouped by channel.

    Parameters
    ----------
    events
        Canonical spike-event table containing ``time_s`` and grouping columns.
    method
        Burst detector to apply: ``"maxinterval"`` or ``"logisi"``.
    group_by
        Columns used to define independent spike trains.
    **kwargs
        Detector-specific keyword arguments.

    Returns
    -------
    pandas.DataFrame
        Tidy burst table with group keys prepended.

    Examples
    --------
    >>> events = pd.DataFrame(
    ...     {"well": ["A1"] * 3, "electrode": ["A1_11"] * 3, "time_s": [0.0, 0.05, 0.1]}
    ... )
    >>> detect_bursts(events).loc[0, "n_spikes"]
    3
    """
    group_columns = list(group_by)
    required = {"time_s", *group_columns}
    missing = sorted(required.difference(events.columns))
    if missing:
        raise MEAValueError(f"events: missing required column(s) {missing}")
    if method not in {"maxinterval", "logisi"}:
        raise MEAValueError(f"events: unsupported burst detection method {method!r}")
    if events.empty:
        return _empty_grouped_bursts(group_columns)

    detector = detect_bursts_maxinterval if method == "maxinterval" else detect_bursts_logisi
    frames: list[pd.DataFrame] = []
    grouped = events.sort_values([*group_columns, "time_s"]).groupby(group_columns, dropna=False)
    for keys, group in grouped:
        key_values = (keys,) if len(group_columns) == 1 else tuple(keys)
        bursts = detector(group["time_s"].to_numpy(dtype=float), **kwargs)
        if bursts.empty:
            continue
        for column, value in zip(group_columns, key_values, strict=True):
            bursts.insert(0, column, value)
        frames.append(bursts)

    if not frames:
        return _empty_grouped_bursts(group_columns)
    return pd.concat(frames, ignore_index=True)
