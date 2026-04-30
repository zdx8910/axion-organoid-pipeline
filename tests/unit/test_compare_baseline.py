import pandas as pd
import pytest

from meaorganoid.compare.baseline import compute_paired_condition_stats, compute_well_delta
from meaorganoid.errors import MEAValueError


def _well_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "well": ["A1", "A1", "A2", "A2", "A3", "A3", "A4", "A4"],
            "condition": [
                "baseline",
                "treatment",
                "baseline",
                "treatment",
                "baseline",
                "treatment",
                "baseline",
                "treatment",
            ],
            "mean_firing_rate_hz": [1.0, 1.5, 2.0, 2.25, 3.0, 2.5, 4.0, 4.75],
            "active_channel_count": [4, 5, 6, 7, 8, 7, 10, 12],
        }
    )


def test_compute_well_delta_returns_nonbaseline_rows_with_deltas() -> None:
    result = compute_well_delta(_well_summary(), baseline_label="baseline")

    assert result["condition"].tolist() == ["treatment"] * 4
    assert result["mean_firing_rate_hz__delta"].tolist() == pytest.approx([0.5, 0.25, -0.5, 0.75])
    assert result["active_channel_count__delta"].tolist() == pytest.approx([1.0, 1.0, -1.0, 2.0])


def test_compute_well_delta_drops_missing_baseline_once(
    caplog: pytest.LogCaptureFixture,
) -> None:
    frame = _well_summary().loc[
        lambda data: ~((data["well"] == "A4") & (data["condition"] == "baseline"))
    ]

    with caplog.at_level("INFO", logger="meaorganoid.compare.baseline"):
        result = compute_well_delta(frame, baseline_label="baseline")

    assert result["well"].tolist() == ["A1", "A2", "A3"]
    assert len(caplog.records) == 1
    assert "A4" in caplog.records[0].getMessage()


def test_compute_well_delta_missing_metric_raises() -> None:
    with pytest.raises(MEAValueError, match="nonexistent"):
        compute_well_delta(_well_summary(), baseline_label="baseline", metrics=["nonexistent"])


def test_paired_condition_stats_identical_distribution_is_not_significant() -> None:
    frame = _well_summary()
    frame.loc[frame["condition"] == "treatment", "mean_firing_rate_hz"] = frame.loc[
        frame["condition"] == "baseline", "mean_firing_rate_hz"
    ].to_numpy()

    result = compute_paired_condition_stats(
        frame,
        condition_a="baseline",
        condition_b="treatment",
        metrics=["mean_firing_rate_hz"],
    )

    assert result.loc[0, "mean_diff"] == pytest.approx(0.0)
    assert result.loc[0, "wilcoxon_p"] == pytest.approx(1.0)
    assert bool(result.loc[0, "significant"]) is False


def test_paired_condition_stats_deterministic_shift_is_significant() -> None:
    frame = pd.DataFrame(
        {
            "well": [f"A{i}" for i in range(1, 9) for _ in range(2)],
            "condition": ["baseline", "treatment"] * 8,
            "mean_firing_rate_hz": [value for i in range(8) for value in (float(i), float(i + 2))],
            "active_channel_count": [value for i in range(8) for value in (float(i), float(i + 1))],
        }
    )

    result = compute_paired_condition_stats(
        frame,
        condition_a="baseline",
        condition_b="treatment",
        metrics=["mean_firing_rate_hz"],
    )

    assert result.loc[0, "mean_diff"] == pytest.approx(2.0)
    assert bool(result.loc[0, "significant"]) is True


def test_paired_condition_stats_bootstrap_ci_is_reproducible() -> None:
    first = compute_paired_condition_stats(
        _well_summary(),
        condition_a="baseline",
        condition_b="treatment",
    )
    second = compute_paired_condition_stats(
        _well_summary(),
        condition_a="baseline",
        condition_b="treatment",
    )

    assert first[["ci_low", "ci_high"]].equals(second[["ci_low", "ci_high"]])
