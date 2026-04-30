import numpy as np
import pytest

from meaorganoid.bursts.maxinterval import detect_bursts_maxinterval
from meaorganoid.errors import MEAValueError


def test_maxinterval_detects_three_known_bursts() -> None:
    times = np.array([0.0, 0.05, 0.1, 1.0, 1.04, 1.08, 2.0, 2.03, 2.06])

    bursts = detect_bursts_maxinterval(times)

    assert bursts["start_s"].tolist() == pytest.approx([0.0, 1.0, 2.0])
    assert bursts["end_s"].tolist() == pytest.approx([0.1, 1.08, 2.06])
    assert bursts["n_spikes"].tolist() == [3, 3, 3]


def test_maxinterval_empty_train_returns_empty_dataframe() -> None:
    bursts = detect_bursts_maxinterval(np.array([]))

    assert bursts.empty
    assert bursts.columns.tolist() == [
        "burst_index",
        "start_s",
        "end_s",
        "duration_s",
        "n_spikes",
        "mean_isi_s",
        "intra_burst_rate_hz",
    ]


def test_maxinterval_non_monotonic_train_raises() -> None:
    with pytest.raises(MEAValueError, match="not monotonic"):
        detect_bursts_maxinterval(np.array([0.0, 0.2, 0.1]))


def test_maxinterval_all_isis_within_start_threshold_is_one_burst() -> None:
    times = np.array([0.0, 0.05, 0.10, 0.15, 0.20])

    bursts = detect_bursts_maxinterval(times)

    assert len(bursts) == 1
    assert bursts.loc[0, "start_s"] == pytest.approx(0.0)
    assert bursts.loc[0, "end_s"] == pytest.approx(0.20)
    assert bursts.loc[0, "n_spikes"] == 5


def test_maxinterval_all_isis_exceed_start_threshold_is_zero_bursts() -> None:
    times = np.array([0.0, 0.2, 0.4, 0.6])

    bursts = detect_bursts_maxinterval(times)

    assert bursts.empty
