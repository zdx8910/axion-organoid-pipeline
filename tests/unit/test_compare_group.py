import pandas as pd
import pytest

from meaorganoid.compare.group import GROUP_COMPARISON_COLUMNS, compare_groups
from meaorganoid.errors import MEAValueError


def _two_group_frame(shift: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "well": [f"A{i}" for i in range(10)] + [f"B{i}" for i in range(10)],
            "group": ["control"] * 10 + ["treatment"] * 10,
            "mean_firing_rate_hz": [float(i) for i in range(10)]
            + [float(i) + shift for i in range(10)],
            "active_channel_count": [float(i % 4 + 4) for i in range(10)]
            + [float(i % 4 + 4 + shift) for i in range(10)],
            "burst_rate_hz": [float(i) / 10.0 for i in range(10)]
            + [float(i) / 10.0 + shift for i in range(10)],
        }
    )


def test_compare_groups_identical_distribution_is_not_significant() -> None:
    result = compare_groups(
        _two_group_frame(),
        group_col="group",
        metrics=["mean_firing_rate_hz"],
        correction="none",
    )

    assert list(result.columns) == list(GROUP_COMPARISON_COLUMNS)
    assert result.loc[0, "p_raw"] == pytest.approx(1.0)
    assert bool(result.loc[0, "significant"]) is False


def test_compare_groups_shifted_distribution_is_significant_with_positive_effect() -> None:
    result = compare_groups(
        _two_group_frame(shift=10.0),
        group_col="group",
        metrics=["mean_firing_rate_hz"],
        correction="none",
    )

    assert result.loc[0, "median_b"] > result.loc[0, "median_a"]
    assert result.loc[0, "p_raw"] < 0.001
    assert result.loc[0, "effect_size_r"] > 0.0
    assert bool(result.loc[0, "significant"]) is True


def test_compare_groups_three_groups_uses_pairwise_rank_rows() -> None:
    frame = _two_group_frame(shift=2.0)
    extra = frame.loc[frame["group"] == "treatment"].copy()
    extra["group"] = "high"
    extra["well"] = [f"C{i}" for i in range(len(extra))]
    extra["mean_firing_rate_hz"] = extra["mean_firing_rate_hz"] + 5.0

    result = compare_groups(
        pd.concat([frame, extra], ignore_index=True),
        group_col="group",
        metrics=["mean_firing_rate_hz"],
    )

    assert len(result) == 3
    assert set(result["group_a"]).union(result["group_b"]) == {"control", "high", "treatment"}


def test_compare_groups_logs_groups_below_minimum(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("INFO", logger="meaorganoid.compare.group"):
        result = compare_groups(
            _two_group_frame(),
            group_col="group",
            metrics=["mean_firing_rate_hz"],
            min_n_per_group=20,
        )

    assert result.empty
    assert "Dropped groups" in caplog.records[0].getMessage()


def test_compare_groups_multiple_testing_corrections_differ() -> None:
    frame = _two_group_frame(shift=3.0)
    none = compare_groups(frame, group_col="group", correction="none")
    holm = compare_groups(frame, group_col="group", correction="holm")
    bh = compare_groups(frame, group_col="group", correction="bh")

    assert none["p_adj"].tolist() == pytest.approx(none["p_raw"].tolist())
    assert holm["p_adj"].tolist() != pytest.approx(none["p_adj"].tolist())
    assert bh["p_adj"].tolist() != pytest.approx(holm["p_adj"].tolist())


def test_compare_groups_missing_metric_raises() -> None:
    with pytest.raises(MEAValueError, match="missing"):
        compare_groups(_two_group_frame(), group_col="group", metrics=["not_a_metric"])
