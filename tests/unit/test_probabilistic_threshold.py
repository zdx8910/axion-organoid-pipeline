import numpy as np
import pandas as pd
import pytest

from meaorganoid.connectivity.threshold import probabilistic_threshold
from meaorganoid.errors import MEAValueError


def _events_from_trains(trains: dict[str, np.ndarray]) -> pd.DataFrame:
    rows = [
        {"well": "A1", "electrode": electrode, "time_s": float(time)}
        for electrode, train in trains.items()
        for time in train
    ]
    return pd.DataFrame(rows)


def test_probabilistic_threshold_is_reproducible_with_seed() -> None:
    base = np.linspace(0.1, 4.9, 30)
    events = _events_from_trains({"A1_11": base, "A1_12": base + 0.002})

    first, first_mask = probabilistic_threshold(
        events, well="A1", lag_s=0.01, recording_duration_s=5.0, n_iterations=20, min_spikes=10
    )
    second, second_mask = probabilistic_threshold(
        events, well="A1", lag_s=0.01, recording_duration_s=5.0, n_iterations=20, min_spikes=10
    )

    assert np.array_equal(first, second)
    assert np.array_equal(first_mask, second_mask)


def test_probabilistic_threshold_independent_poisson_is_mostly_not_significant() -> None:
    rng = np.random.default_rng(12)
    trains = {
        f"A1_{row}{col}": np.sort(rng.uniform(0.0, 10.0, size=25))
        for row, col in [(1, 1), (1, 2), (2, 1), (2, 2)]
    }
    _, mask = probabilistic_threshold(
        _events_from_trains(trains),
        well="A1",
        lag_s=0.005,
        recording_duration_s=10.0,
        n_iterations=30,
        min_spikes=20,
    )

    off_diagonal = mask[~np.eye(mask.shape[0], dtype=bool)]
    assert float(np.mean(off_diagonal)) < 0.10


def test_probabilistic_threshold_strongly_coupled_trains_are_significant() -> None:
    base = np.linspace(0.1, 8.0, 40)
    events = _events_from_trains(
        {
            "A1_11": base,
            "A1_12": base + 0.001,
            "A1_21": base + 0.002,
        }
    )

    _, mask = probabilistic_threshold(
        events,
        well="A1",
        lag_s=0.01,
        recording_duration_s=10.0,
        n_iterations=30,
        min_spikes=20,
    )

    off_diagonal = mask[~np.eye(mask.shape[0], dtype=bool)]
    assert float(np.mean(off_diagonal)) > 0.80


def test_probabilistic_threshold_rejects_zero_iterations() -> None:
    with pytest.raises(MEAValueError, match="n_iterations"):
        probabilistic_threshold(
            _events_from_trains({"A1_11": np.array([1.0]), "A1_12": np.array([1.0])}),
            well="A1",
            lag_s=0.01,
            recording_duration_s=2.0,
            n_iterations=0,
            min_spikes=1,
        )
