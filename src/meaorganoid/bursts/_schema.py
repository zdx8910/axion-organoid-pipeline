"""Shared schema helpers for Workflow B burst detection."""

import numpy as np
import pandas as pd

from meaorganoid.errors import MEAValueError

BURST_COLUMNS = (
    "burst_index",
    "start_s",
    "end_s",
    "duration_s",
    "n_spikes",
    "mean_isi_s",
    "intra_burst_rate_hz",
)


def empty_bursts() -> pd.DataFrame:
    """Return an empty burst table with the public Workflow B schema."""
    return pd.DataFrame(
        {
            "burst_index": pd.Series(dtype="int64"),
            "start_s": pd.Series(dtype="float64"),
            "end_s": pd.Series(dtype="float64"),
            "duration_s": pd.Series(dtype="float64"),
            "n_spikes": pd.Series(dtype="int64"),
            "mean_isi_s": pd.Series(dtype="float64"),
            "intra_burst_rate_hz": pd.Series(dtype="float64"),
        }
    )


def validate_spike_times(spike_times_s: np.ndarray) -> np.ndarray:
    """Validate and normalize a spike-time array for burst detection."""
    times = np.asarray(spike_times_s, dtype=float)
    if times.ndim != 1:
        raise MEAValueError("spike_times_s: expected a one-dimensional array")
    if times.size > 1 and bool(np.any(np.diff(times) < 0)):
        raise MEAValueError("spike_times_s: input is not monotonic")
    return times


def bursts_from_segments(times: np.ndarray, segments: list[tuple[int, int]]) -> pd.DataFrame:
    """Build the public burst table from inclusive spike-index segments."""
    if not segments:
        return empty_bursts()

    rows: list[dict[str, float | int]] = []
    for burst_index, (start_index, end_index) in enumerate(segments):
        burst_times = times[start_index : end_index + 1]
        duration = float(burst_times[-1] - burst_times[0])
        intervals = np.diff(burst_times)
        rows.append(
            {
                "burst_index": burst_index,
                "start_s": float(burst_times[0]),
                "end_s": float(burst_times[-1]),
                "duration_s": duration,
                "n_spikes": int(burst_times.size),
                "mean_isi_s": float(np.mean(intervals)) if intervals.size else np.nan,
                "intra_burst_rate_hz": float(burst_times.size / duration)
                if duration > 0
                else np.inf,
            }
        )
    return pd.DataFrame(rows, columns=BURST_COLUMNS)
