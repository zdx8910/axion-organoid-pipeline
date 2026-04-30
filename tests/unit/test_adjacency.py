import numpy as np
import pandas as pd

from meaorganoid.connectivity.adjacency import build_sttc_adjacency


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "well": ["A1"] * 23,
            "electrode": ["A1_11"] * 10 + ["A1_12"] * 10 + ["A1_21"] * 3,
            "time_s": [float(i) / 10.0 for i in range(10)]
            + [float(i) / 10.0 + 0.01 for i in range(10)]
            + [0.1, 0.2, 0.3],
        }
    )


def test_build_sttc_adjacency_is_symmetric_with_unit_diagonal() -> None:
    adjacency, labels = build_sttc_adjacency(
        _events(),
        well="A1",
        lag_s=0.05,
        recording_duration_s=2.0,
        min_spikes=3,
    )

    assert labels == ["A1_11", "A1_12", "A1_21"]
    assert np.allclose(adjacency, adjacency.T, equal_nan=True)
    assert np.allclose(np.diag(adjacency), 1.0)
    off_diagonal = adjacency[~np.eye(adjacency.shape[0], dtype=bool)]
    assert np.nanmin(off_diagonal) >= -1.0
    assert np.nanmax(off_diagonal) <= 1.0


def test_build_sttc_adjacency_filters_min_spikes() -> None:
    adjacency, labels = build_sttc_adjacency(
        _events(),
        well="A1",
        lag_s=0.05,
        recording_duration_s=2.0,
        min_spikes=10,
    )

    assert labels == ["A1_11", "A1_12"]
    assert adjacency.shape == (2, 2)


def test_build_sttc_adjacency_empty_well_returns_empty_matrix() -> None:
    adjacency, labels = build_sttc_adjacency(
        _events(),
        well="B2",
        lag_s=0.05,
        recording_duration_s=2.0,
    )

    assert labels == []
    assert adjacency.shape == (0, 0)
