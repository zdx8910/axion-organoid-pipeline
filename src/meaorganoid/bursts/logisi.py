"""Workflow B (Fig. 2): logISI burst detection."""

import logging
from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

from meaorganoid.bursts._schema import bursts_from_segments, empty_bursts, validate_spike_times

LOGGER = logging.getLogger(__name__)


def _derive_logisi_threshold(intervals: np.ndarray, *, void_parameter: float) -> float:
    positive_intervals = intervals[intervals > 0]
    if positive_intervals.size < 3:
        return float(np.inf)

    log_intervals = np.log10(positive_intervals)
    counts, edges = np.histogram(
        log_intervals,
        bins=min(128, max(16, positive_intervals.size // 2)),
    )
    centers = (edges[:-1] + edges[1:]) / 2.0
    smoothed = gaussian_filter1d(counts.astype(float), sigma=1.0)

    peak_indices, _ = find_peaks(smoothed)
    endpoint_peaks: list[int] = []
    if smoothed.size > 1 and smoothed[0] > smoothed[1]:
        endpoint_peaks.append(0)
    if smoothed.size > 1 and smoothed[-1] > smoothed[-2]:
        endpoint_peaks.append(smoothed.size - 1)
    if endpoint_peaks:
        peak_indices = np.unique(np.concatenate((peak_indices, np.array(endpoint_peaks))))
    if peak_indices.size < 2:
        threshold = float(10 ** np.median(log_intervals))
        LOGGER.info("Derived logISI threshold %.6f s from median log-ISI", threshold)
        return threshold

    ordered_peaks = peak_indices[np.argsort(centers[peak_indices])]
    for left_peak, right_peak in pairwise(ordered_peaks):
        if right_peak <= left_peak + 1:
            continue
        valley_slice = smoothed[left_peak : right_peak + 1]
        min_height = float(np.min(valley_slice))
        valley_offsets = np.flatnonzero(valley_slice == min_height)
        valley_offset = int(valley_offsets[valley_offsets.size // 2])
        valley_index = left_peak + valley_offset
        valley_height = float(smoothed[valley_index])
        left_height = float(smoothed[left_peak])
        right_height = float(smoothed[right_peak])
        reference_height = max(min(left_height, right_height), 1.0)
        void = 1.0 - (valley_height / reference_height)
        if void >= void_parameter:
            threshold = float(10 ** centers[valley_index])
            LOGGER.info("Derived logISI threshold %.6f s", threshold)
            return threshold

    gap_index = int(np.argmax(np.diff(centers[ordered_peaks])))
    threshold = float(
        10 ** ((centers[ordered_peaks[gap_index]] + centers[ordered_peaks[gap_index + 1]]) / 2.0)
    )
    LOGGER.info("Derived logISI threshold %.6f s from peak gap", threshold)
    return threshold


def detect_bursts_logisi(
    spike_times_s: np.ndarray,
    *,
    isi_threshold_s: float | None = None,
    min_spikes_in_burst: int = 3,
    void_parameter: float = 0.7,
) -> pd.DataFrame:
    """Detect single-channel bursts using a log-ISI threshold.

    Parameters
    ----------
    spike_times_s
        Sorted, monotonic spike times in seconds for one electrode.
    isi_threshold_s
        ISI threshold in seconds. When omitted, it is derived from a smoothed log-ISI histogram.
    min_spikes_in_burst
        Minimum accepted number of spikes per burst.
    void_parameter
        Minimum trough depth between log-ISI peaks when deriving the threshold.

    Returns
    -------
    pandas.DataFrame
        Burst table with the public Workflow B schema.

    Examples
    --------
    >>> import numpy as np
    >>> detect_bursts_logisi(np.array([0.0, 0.05, 0.1]), isi_threshold_s=0.1).loc[0, "n_spikes"]
    3
    """
    times = validate_spike_times(spike_times_s)
    if times.size < min_spikes_in_burst:
        return empty_bursts()

    intervals = np.diff(times)
    threshold = (
        _derive_logisi_threshold(intervals, void_parameter=void_parameter)
        if isi_threshold_s is None
        else isi_threshold_s
    )
    within_threshold = intervals <= threshold
    padded = np.concatenate(([False], within_threshold, [False]))
    changes = np.flatnonzero(padded[1:] != padded[:-1])
    run_starts = changes[::2]
    run_ends = changes[1::2] - 1
    segments = [
        (int(start), int(end + 1))
        for start, end in zip(run_starts, run_ends, strict=True)
        if (end - start + 2) >= min_spikes_in_burst
    ]
    return bursts_from_segments(times, segments)
