"""Workflow G (Fig. 7): probabilistic connectivity thresholding."""

from itertools import combinations

import numpy as np
import pandas as pd

from meaorganoid.connectivity.adjacency import _spike_trains_for_well, build_sttc_adjacency
from meaorganoid.connectivity.sttc import _sttc_rows_against_train
from meaorganoid.errors import MEAValueError


def probabilistic_threshold(
    events: pd.DataFrame,
    *,
    well: str,
    lag_s: float,
    recording_duration_s: float,
    n_iterations: int = 200,
    percentile: float = 95.0,
    seed: int | None = 0,
    min_spikes: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    """Threshold STTC edges against circular-shift null distributions.

    Parameters
    ----------
    events
        Canonical spike-event table with ``well``, ``electrode``, and ``time_s`` columns.
    well
        Well label to include.
    lag_s
        STTC lag window half-width in seconds.
    recording_duration_s
        Recording duration in seconds.
    n_iterations
        Number of circular shifts per electrode pair.
    percentile
        Percentile of the null distribution used as the edge threshold.
    seed
        Seed for ``numpy.random.default_rng``.
    min_spikes
        Minimum spike count required for an electrode to be retained.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Thresholded adjacency matrix and boolean significance mask.

    Examples
    --------
    >>> events = pd.DataFrame(
    ...     {
    ...         "well": ["A1"] * 4,
    ...         "electrode": ["A1_11", "A1_11", "A1_12", "A1_12"],
    ...         "time_s": [1, 2, 1, 2],
    ...     }
    ... )
    >>> adjacency, mask = probabilistic_threshold(
    ...     events, well="A1", lag_s=0.01, recording_duration_s=3, n_iterations=2, min_spikes=2
    ... )
    >>> adjacency.shape == mask.shape
    True
    """
    if n_iterations <= 0:
        raise MEAValueError("connectivity: n_iterations must be greater than 0")
    if recording_duration_s <= 0:
        raise MEAValueError("connectivity: recording_duration_s must be greater than 0")

    real_adjacency, labels = build_sttc_adjacency(
        events,
        well=well,
        lag_s=lag_s,
        recording_duration_s=recording_duration_s,
        min_spikes=min_spikes,
    )
    if not labels:
        empty = np.zeros((0, 0), dtype=bool)
        return real_adjacency, empty

    trains = _spike_trains_for_well(events, well=well, min_spikes=min_spikes)
    rng = np.random.default_rng(seed)
    thresholded = np.zeros_like(real_adjacency)
    significance = np.zeros(real_adjacency.shape, dtype=bool)
    np.fill_diagonal(thresholded, 1.0)
    np.fill_diagonal(significance, True)

    pair_indices = list(combinations(range(len(labels)), 2))
    shifts = rng.uniform(0.0, recording_duration_s, size=(len(pair_indices), n_iterations))
    for pair_index, (left, right) in enumerate(pair_indices):
        left_train = trains[labels[left]]
        right_train = trains[labels[right]]
        shifted = np.sort(
            (right_train[np.newaxis, :] + shifts[pair_index, :, np.newaxis]) % recording_duration_s,
            axis=1,
        )
        null_values = _sttc_rows_against_train(
            left_train,
            shifted,
            lag_s=lag_s,
            recording_duration_s=recording_duration_s,
        )
        cutoff = float(np.nanpercentile(null_values, percentile))
        value = real_adjacency[left, right]
        is_significant = bool(np.isfinite(value) and value > cutoff)
        significance[left, right] = is_significant
        significance[right, left] = is_significant
        if is_significant:
            thresholded[left, right] = value
            thresholded[right, left] = value

    return thresholded, significance
