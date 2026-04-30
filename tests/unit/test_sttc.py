import numpy as np
import pytest

from meaorganoid.connectivity.sttc import compute_sttc


def test_compute_sttc_identical_trains_is_one() -> None:
    train = np.array([1.0, 2.0, 3.0])

    assert compute_sttc(train, train, lag_s=0.01, recording_duration_s=10.0) == pytest.approx(1.0)


def test_compute_sttc_empty_train_returns_nan() -> None:
    result = compute_sttc(np.array([]), np.array([1.0]), lag_s=0.01, recording_duration_s=10.0)

    assert np.isnan(result)


def test_compute_sttc_disjoint_trains_is_near_zero() -> None:
    result = compute_sttc(
        np.array([1.0, 3.0]),
        np.array([2.0, 4.0]),
        lag_s=0.01,
        recording_duration_s=5.0,
    )

    assert abs(result) < 0.02


def test_compute_sttc_matches_hand_computed_example() -> None:
    result = compute_sttc(
        np.array([1.0, 3.0]),
        np.array([1.05, 4.0]),
        lag_s=0.1,
        recording_duration_s=5.0,
    )

    assert result == pytest.approx(0.4375)
