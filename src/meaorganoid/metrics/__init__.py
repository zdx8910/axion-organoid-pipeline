"""Firing-rate and ISI metrics for Axion MEA spike events."""

from typing import cast

import numpy as np
import pandas as pd

from meaorganoid.errors import MEAValueError


def _duration_from_spikes(spikes: pd.DataFrame) -> float:
    if spikes.empty:
        return 0.0
    return float(spikes["time_s"].max() - spikes["time_s"].min())


def compute_channel_summary(
    spikes: pd.DataFrame,
    recording_duration_s: float | None = None,
    active_threshold_hz: float = 0.1,
) -> pd.DataFrame:
    """Compute per-channel firing-rate and ISI summary metrics.

    Parameters
    ----------
    spikes
        Canonical spike-event table from :func:`meaorganoid.io.read_axion_spike_csv`.
    recording_duration_s
        Recording duration in seconds. When omitted, the duration is inferred from spike times.
    active_threshold_hz
        Minimum firing rate used to mark an electrode as active.

    Returns
    -------
    pandas.DataFrame
        Per-channel summary table.

    Examples
    --------
    >>> spikes = pd.DataFrame(
    ...     {"well": ["A1", "A1"], "electrode": ["A1_11", "A1_11"], "time_s": [0.0, 1.0]}
    ... )
    >>> int(compute_channel_summary(spikes, recording_duration_s=2.0).loc[0, "spike_count"])
    2
    """
    if "time_s" not in spikes.columns or "electrode" not in spikes.columns:
        raise MEAValueError("spikes: missing required column 'time_s' or 'electrode'")

    duration = (
        _duration_from_spikes(spikes) if recording_duration_s is None else recording_duration_s
    )
    if duration <= 0:
        raise MEAValueError("spikes: recording_duration_s must be greater than 0")

    group_columns = ["electrode"] if "well" not in spikes.columns else ["well", "electrode"]
    rows: list[dict[str, object]] = []
    for keys, group in spikes.sort_values("time_s").groupby(group_columns, dropna=False):
        key_values = (keys,) if isinstance(keys, str) else tuple(keys)
        row = dict(zip(group_columns, key_values, strict=True))
        times = group["time_s"].to_numpy(dtype=float)
        intervals = np.diff(times)
        spike_count = int(times.size)
        firing_rate_hz = spike_count / duration
        row.update(
            {
                "spike_count": spike_count,
                "recording_duration_s": duration,
                "firing_rate_hz": firing_rate_hz,
                "isi_mean_s": float(np.mean(intervals)) if intervals.size else np.nan,
                "isi_median_s": float(np.median(intervals)) if intervals.size else np.nan,
                "is_active": bool(firing_rate_hz >= active_threshold_hz),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def compute_well_summary(channel_summary: pd.DataFrame) -> pd.DataFrame:
    """Aggregate channel metrics to the well level.

    Parameters
    ----------
    channel_summary
        Per-channel summary table from :func:`compute_channel_summary`.

    Returns
    -------
    pandas.DataFrame
        Per-well summary table.

    Examples
    --------
    >>> channels = pd.DataFrame(
    ...     {
    ...         "well": ["A1", "A1"],
    ...         "electrode": ["A1_11", "A1_12"],
    ...         "spike_count": [2, 4],
    ...         "recording_duration_s": [2.0, 2.0],
    ...         "firing_rate_hz": [1.0, 2.0],
    ...         "is_active": [True, True],
    ...     }
    ... )
    >>> int(compute_well_summary(channels).loc[0, "total_spike_count"])
    6
    """
    if "well" not in channel_summary.columns:
        frame = channel_summary.copy()
        frame["well"] = "unknown"
    else:
        frame = channel_summary.copy()

    result = (
        frame.groupby("well", dropna=False)
        .agg(
            channel_count=("electrode", "nunique"),
            active_channel_count=("is_active", "sum"),
            total_spike_count=("spike_count", "sum"),
            mean_firing_rate_hz=("firing_rate_hz", "mean"),
            median_firing_rate_hz=("firing_rate_hz", "median"),
            recording_duration_s=("recording_duration_s", "max"),
        )
        .reset_index()
    )
    return cast(pd.DataFrame, result)
