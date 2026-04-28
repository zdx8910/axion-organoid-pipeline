"""Workflow G (Fig. 7): lag-windowed functional connectivity helpers."""

import numpy as np
import pandas as pd

from meaorganoid.errors import MEAValueError


def compute_lag_window_adjacency(spikes: pd.DataFrame, lag_window_s: float = 0.05) -> pd.DataFrame:
    """Compute a simple pairwise lag-window adjacency matrix.

    Parameters
    ----------
    spikes
        Canonical spike-event table with ``time_s`` and ``electrode`` columns.
    lag_window_s
        Maximum lag, in seconds, for counting coincident spikes between channels.

    Returns
    -------
    pandas.DataFrame
        Square adjacency matrix indexed and columned by electrode label.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    if "time_s" not in spikes.columns or "electrode" not in spikes.columns:
        raise MEAValueError("spikes: missing required column 'time_s' or 'electrode'")

    electrodes = sorted(spikes["electrode"].astype(str).unique())
    matrix = pd.DataFrame(0, index=electrodes, columns=electrodes, dtype=int)
    grouped = {
        electrode: group["time_s"].sort_values().to_numpy(dtype=float)
        for electrode, group in spikes.assign(electrode=spikes["electrode"].astype(str)).groupby(
            "electrode"
        )
    }
    for left in electrodes:
        for right in electrodes:
            if left == right:
                continue
            left_times = grouped[left]
            right_times = grouped[right]
            count = 0
            for time in left_times:
                count += int(np.any(np.abs(right_times - time) <= lag_window_s))
            matrix.loc[left, right] = count
    return matrix
