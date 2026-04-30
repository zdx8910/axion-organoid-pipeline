import re

import numpy as np
import pytest

from meaorganoid.bursts.logisi import detect_bursts_logisi
from meaorganoid.errors import MEAValueError


def test_logisi_detects_three_known_bursts_with_explicit_threshold() -> None:
    times = np.array([0.0, 0.05, 0.1, 1.0, 1.04, 1.08, 2.0, 2.03, 2.06])

    bursts = detect_bursts_logisi(times, isi_threshold_s=0.1)

    assert bursts["start_s"].tolist() == pytest.approx([0.0, 1.0, 2.0])
    assert bursts["end_s"].tolist() == pytest.approx([0.1, 1.08, 2.06])
    assert bursts["n_spikes"].tolist() == [3, 3, 3]


def test_logisi_empty_train_returns_empty_dataframe() -> None:
    bursts = detect_bursts_logisi(np.array([]))

    assert bursts.empty


def test_logisi_non_monotonic_train_raises() -> None:
    with pytest.raises(MEAValueError, match="not monotonic"):
        detect_bursts_logisi(np.array([0.0, 0.2, 0.1]))


def test_logisi_derived_threshold_for_bimodal_distribution(
    caplog: pytest.LogCaptureFixture,
) -> None:
    burst_times = np.arange(0.0, 0.50, 0.01)
    slow_times = np.arange(10.0, 60.0, 1.0)
    times = np.concatenate([burst_times, slow_times])

    with caplog.at_level("INFO", logger="meaorganoid.bursts.logisi"):
        bursts = detect_bursts_logisi(times, isi_threshold_s=None, min_spikes_in_burst=3)

    messages = "\n".join(record.getMessage() for record in caplog.records)
    match = re.search(r"Derived logISI threshold ([0-9.]+) s", messages)
    assert match is not None
    assert float(match.group(1)) == pytest.approx(0.1, rel=0.05)
    assert not bursts.empty
