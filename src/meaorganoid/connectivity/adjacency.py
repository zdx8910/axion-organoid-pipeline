"""Workflow G (Fig. 7): STTC adjacency matrices."""

from itertools import combinations

import numpy as np
import pandas as pd

from meaorganoid.connectivity.sttc import compute_sttc
from meaorganoid.errors import MEAValueError


def _spike_trains_for_well(
    events: pd.DataFrame,
    *,
    well: str,
    min_spikes: int,
) -> dict[str, np.ndarray]:
    required = {"well", "electrode", "time_s"}
    missing = sorted(required.difference(events.columns))
    if missing:
        raise MEAValueError(f"events: missing required column(s) {missing}")

    well_events = events.loc[events["well"].astype(str) == well].copy()
    if well_events.empty:
        return {}
    trains = {
        str(electrode): group["time_s"].sort_values().to_numpy(dtype=float)
        for electrode, group in well_events.assign(
            electrode=well_events["electrode"].astype(str)
        ).groupby("electrode", sort=True)
    }
    return {electrode: train for electrode, train in trains.items() if train.size >= min_spikes}


def build_sttc_adjacency(
    events: pd.DataFrame,
    *,
    well: str,
    lag_s: float,
    recording_duration_s: float,
    min_spikes: int = 10,
) -> tuple[np.ndarray, list[str]]:
    """Build a symmetric STTC adjacency matrix for one well.

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
    min_spikes
        Minimum spike count required for an electrode to be retained.

    Returns
    -------
    tuple[numpy.ndarray, list[str]]
        Square adjacency matrix and electrode labels matching matrix order.

    Examples
    --------
    >>> events = pd.DataFrame(
    ...     {
    ...         "well": ["A1"] * 4,
    ...         "electrode": ["A1_11", "A1_11", "A1_12", "A1_12"],
    ...         "time_s": [1, 2, 1, 2],
    ...     }
    ... )
    >>> matrix, labels = build_sttc_adjacency(
    ...     events, well="A1", lag_s=0.01, recording_duration_s=3, min_spikes=2
    ... )
    >>> labels
    ['A1_11', 'A1_12']
    >>> matrix.shape
    (2, 2)
    """
    trains = _spike_trains_for_well(events, well=well, min_spikes=min_spikes)
    labels = sorted(trains)
    if not labels:
        return np.zeros((0, 0), dtype=float), []

    adjacency = np.full((len(labels), len(labels)), np.nan, dtype=float)
    np.fill_diagonal(adjacency, 1.0)
    for left, right in combinations(range(len(labels)), 2):
        value = compute_sttc(
            trains[labels[left]],
            trains[labels[right]],
            lag_s=lag_s,
            recording_duration_s=recording_duration_s,
        )
        adjacency[left, right] = value
        adjacency[right, left] = value
    return adjacency, labels
