"""Workflow B (Fig. 2): MaxInterval burst detection."""

import numpy as np
import pandas as pd

from meaorganoid.bursts._schema import bursts_from_segments, empty_bursts, validate_spike_times


def _candidate_segments(
    times: np.ndarray,
    *,
    max_isi_start_s: float,
    max_isi_end_s: float,
) -> list[tuple[int, int]]:
    intervals = np.diff(times)
    if intervals.size == 0:
        return []

    within_end = intervals <= max_isi_end_s
    padded = np.concatenate(([False], within_end, [False]))
    changes = np.flatnonzero(padded[1:] != padded[:-1])
    run_starts = changes[::2]
    run_ends = changes[1::2] - 1

    candidates: list[tuple[int, int]] = []
    for run_start, run_end in zip(run_starts, run_ends, strict=True):
        run_intervals = intervals[run_start : run_end + 1]
        if bool(np.any(run_intervals <= max_isi_start_s)):
            candidates.append((int(run_start), int(run_end + 1)))
    return candidates


def _merge_close_segments(
    times: np.ndarray,
    segments: list[tuple[int, int]],
    *,
    min_ibi_s: float,
) -> list[tuple[int, int]]:
    if not segments:
        return []

    merged = [segments[0]]
    for start_index, end_index in segments[1:]:
        previous_start, previous_end = merged[-1]
        ibi = float(times[start_index] - times[previous_end])
        if ibi < min_ibi_s:
            merged[-1] = (previous_start, end_index)
        else:
            merged.append((start_index, end_index))
    return merged


def detect_bursts_maxinterval(
    spike_times_s: np.ndarray,
    *,
    max_isi_start_s: float = 0.170,
    max_isi_end_s: float = 0.300,
    min_ibi_s: float = 0.200,
    min_burst_duration_s: float = 0.010,
    min_spikes_in_burst: int = 3,
) -> pd.DataFrame:
    """Detect single-channel bursts using the MaxInterval method.

    Parameters
    ----------
    spike_times_s
        Sorted, monotonic spike times in seconds for one electrode.
    max_isi_start_s
        Maximum ISI that can start a candidate burst.
    max_isi_end_s
        Maximum ISI allowed while extending a candidate burst.
    min_ibi_s
        Minimum inter-burst interval; closer candidates are merged.
    min_burst_duration_s
        Minimum accepted burst duration in seconds.
    min_spikes_in_burst
        Minimum accepted number of spikes per burst.

    Returns
    -------
    pandas.DataFrame
        Burst table with the public Workflow B schema.

    Examples
    --------
    >>> import numpy as np
    >>> int(detect_bursts_maxinterval(np.array([0.0, 0.05, 0.1])).loc[0, "n_spikes"])
    3
    """
    times = validate_spike_times(spike_times_s)
    if times.size < min_spikes_in_burst:
        return empty_bursts()

    candidates = _candidate_segments(
        times,
        max_isi_start_s=max_isi_start_s,
        max_isi_end_s=max_isi_end_s,
    )
    merged = _merge_close_segments(times, candidates, min_ibi_s=min_ibi_s)
    filtered = [
        (start, end)
        for start, end in merged
        if (end - start + 1) >= min_spikes_in_burst
        and float(times[end] - times[start]) >= min_burst_duration_s
    ]
    return bursts_from_segments(times, filtered)
