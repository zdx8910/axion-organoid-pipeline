"""Workflow G (Fig. 7): Spike Time Tiling Coefficient."""

import numpy as np
from numpy.typing import NDArray


def _as_sorted_train(spike_train: np.ndarray) -> NDArray[np.float64]:
    train = np.asarray(spike_train, dtype=float)
    if train.ndim != 1:
        raise ValueError("spike trains must be 1-D arrays")
    return np.sort(train)


def _tiled_fraction(spike_train: np.ndarray, *, lag_s: float, recording_duration_s: float) -> float:
    if spike_train.size == 0 or recording_duration_s <= 0:
        return 0.0
    starts = np.clip(spike_train - lag_s, 0.0, recording_duration_s)
    ends = np.clip(spike_train + lag_s, 0.0, recording_duration_s)
    cumulative_ends = np.maximum.accumulate(ends)
    group_starts = np.r_[0, np.flatnonzero(starts[1:] > cumulative_ends[:-1]) + 1]
    merged_starts = starts[group_starts]
    merged_ends = np.maximum.reduceat(ends, group_starts)
    return float(np.sum(merged_ends - merged_starts) / recording_duration_s)


def _tiled_fraction_rows(
    spike_trains: np.ndarray, *, lag_s: float, recording_duration_s: float
) -> NDArray[np.float64]:
    if spike_trains.size == 0 or recording_duration_s <= 0:
        return np.zeros(spike_trains.shape[0], dtype=float)
    starts = np.clip(spike_trains - lag_s, 0.0, recording_duration_s)
    ends = np.clip(spike_trains + lag_s, 0.0, recording_duration_s)
    cumulative_ends = np.maximum.accumulate(ends, axis=1)
    group_start_mask = np.concatenate(
        [
            np.ones((spike_trains.shape[0], 1), dtype=bool),
            starts[:, 1:] > cumulative_ends[:, :-1],
        ],
        axis=1,
    )
    group_end_mask = np.concatenate(
        [group_start_mask[:, 1:], np.ones((spike_trains.shape[0], 1), dtype=bool)],
        axis=1,
    )
    covered = np.sum(cumulative_ends * group_end_mask, axis=1) - np.sum(
        starts * group_start_mask, axis=1
    )
    return np.asarray(covered / recording_duration_s, dtype=float)


def _proportion_close(source: np.ndarray, target: np.ndarray, *, lag_s: float) -> float:
    if source.size == 0 or target.size == 0:
        return 0.0
    insertion = np.searchsorted(target, source)
    previous_index = np.clip(insertion - 1, 0, target.size - 1)
    next_index = np.clip(insertion, 0, target.size - 1)
    previous_close = np.abs(source - target[previous_index]) <= lag_s
    next_close = np.abs(source - target[next_index]) <= lag_s
    return float(np.mean(previous_close | next_close))


def _proportion_close_rows(
    source: np.ndarray, targets: np.ndarray, *, lag_s: float
) -> NDArray[np.float64]:
    if source.size == 0 or targets.size == 0:
        return np.zeros(targets.shape[0], dtype=float)
    close = np.abs(source[np.newaxis, :, np.newaxis] - targets[:, np.newaxis, :]) <= lag_s
    return np.asarray(np.mean(np.any(close, axis=2), axis=1), dtype=float)


def _proportion_rows_close(
    sources: np.ndarray, target: np.ndarray, *, lag_s: float
) -> NDArray[np.float64]:
    if sources.size == 0 or target.size == 0:
        return np.zeros(sources.shape[0], dtype=float)
    close = np.abs(sources[:, :, np.newaxis] - target[np.newaxis, np.newaxis, :]) <= lag_s
    return np.asarray(np.mean(np.any(close, axis=2), axis=1), dtype=float)


def _sttc_from_components(
    *,
    proportion_a: float,
    proportion_b: float,
    tiled_a: float,
    tiled_b: float,
) -> float:
    denom_a = 1.0 - proportion_a * tiled_b
    denom_b = 1.0 - proportion_b * tiled_a
    term_a = 0.0 if np.isclose(denom_a, 0.0) else (proportion_a - tiled_b) / denom_a
    term_b = 0.0 if np.isclose(denom_b, 0.0) else (proportion_b - tiled_a) / denom_b
    return float(np.clip(0.5 * (term_a + term_b), -1.0, 1.0))


def _sttc_rows_against_train(
    spike_train_a: np.ndarray,
    spike_trains_b: np.ndarray,
    *,
    lag_s: float,
    recording_duration_s: float,
) -> NDArray[np.float64]:
    train_a = _as_sorted_train(spike_train_a)
    trains_b = np.sort(np.asarray(spike_trains_b, dtype=float), axis=1)
    tiled_a = _tiled_fraction(train_a, lag_s=lag_s, recording_duration_s=recording_duration_s)
    tiled_b = _tiled_fraction_rows(trains_b, lag_s=lag_s, recording_duration_s=recording_duration_s)
    proportion_a = _proportion_close_rows(train_a, trains_b, lag_s=lag_s)
    proportion_b = _proportion_rows_close(trains_b, train_a, lag_s=lag_s)
    denom_a = 1.0 - proportion_a * tiled_b
    denom_b = 1.0 - proportion_b * tiled_a
    term_a = np.divide(
        proportion_a - tiled_b,
        denom_a,
        out=np.zeros_like(proportion_a),
        where=~np.isclose(denom_a, 0.0),
    )
    term_b = np.divide(
        proportion_b - tiled_a,
        denom_b,
        out=np.zeros_like(proportion_b),
        where=~np.isclose(denom_b, 0.0),
    )
    return np.asarray(np.clip(0.5 * (term_a + term_b), -1.0, 1.0), dtype=float)


def compute_sttc(
    spike_train_a: np.ndarray,
    spike_train_b: np.ndarray,
    *,
    lag_s: float,
    recording_duration_s: float,
) -> float:
    """Compute the Spike Time Tiling Coefficient between two spike trains.

    Parameters
    ----------
    spike_train_a
        Sorted 1-D spike times in seconds for the first electrode.
    spike_train_b
        Sorted 1-D spike times in seconds for the second electrode.
    lag_s
        Coincidence window half-width in seconds.
    recording_duration_s
        Recording duration in seconds.

    Returns
    -------
    float
        STTC value in ``[-1.0, 1.0]``. Returns ``numpy.nan`` when either train is empty.

    Examples
    --------
    >>> train = np.array([1.0, 2.0, 3.0])
    >>> compute_sttc(train, train, lag_s=0.01, recording_duration_s=10.0)
    1.0
    """
    train_a = _as_sorted_train(spike_train_a)
    train_b = _as_sorted_train(spike_train_b)
    if train_a.size == 0 or train_b.size == 0:
        return float("nan")

    tiled_a = _tiled_fraction(train_a, lag_s=lag_s, recording_duration_s=recording_duration_s)
    tiled_b = _tiled_fraction(train_b, lag_s=lag_s, recording_duration_s=recording_duration_s)
    proportion_a = _proportion_close(train_a, train_b, lag_s=lag_s)
    proportion_b = _proportion_close(train_b, train_a, lag_s=lag_s)
    return _sttc_from_components(
        proportion_a=proportion_a,
        proportion_b=proportion_b,
        tiled_a=tiled_a,
        tiled_b=tiled_b,
    )
