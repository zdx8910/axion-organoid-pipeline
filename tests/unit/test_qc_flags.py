import pandas as pd

from meaorganoid.qc import QCThresholds, compute_qc_flags


def _manifest() -> pd.DataFrame:
    rows = [
        {
            "recording_id": f"pass_{index}",
            "condition": "control",
            "active_channel_count": 6,
            "recording_duration_s": 120.0,
            "mean_firing_rate_hz": 1.0,
        }
        for index in range(12)
    ]
    rows.extend(
        [
            {
                "recording_id": "outlier_rate",
                "condition": "control",
                "active_channel_count": 6,
                "recording_duration_s": 120.0,
                "mean_firing_rate_hz": 100.0,
            },
            {
                "recording_id": "low_active",
                "condition": "treated",
                "active_channel_count": 3,
                "recording_duration_s": 120.0,
                "mean_firing_rate_hz": 2.0,
            },
            {
                "recording_id": "short_duration",
                "condition": "treated",
                "active_channel_count": 6,
                "recording_duration_s": 30.0,
                "mean_firing_rate_hz": 2.0,
            },
            {
                "recording_id": "two_reasons",
                "condition": "treated",
                "active_channel_count": 2,
                "recording_duration_s": 10.0,
                "mean_firing_rate_hz": 2.0,
            },
        ]
    )
    return pd.DataFrame(rows)


def test_compute_qc_flags_values_types_and_reasons() -> None:
    manifest = _manifest()
    original = manifest.copy(deep=True)

    result = compute_qc_flags(manifest)

    assert manifest.equals(original)
    for column in ("qc_low_active_channels", "qc_short_duration", "qc_outlier_rate"):
        assert str(result[column].dtype) == "bool"
    assert str(result["qc_status"].dtype) in {"object", "str", "string"}
    assert str(result["qc_reasons"].dtype) in {"object", "str", "string"}

    by_id = result.set_index("recording_id")
    assert by_id.loc["pass_0", "qc_status"] == "pass"
    assert by_id.loc["pass_0", "qc_reasons"] == ""
    assert bool(by_id.loc["low_active", "qc_low_active_channels"])
    assert by_id.loc["low_active", "qc_reasons"] == "qc_low_active_channels"
    assert bool(by_id.loc["short_duration", "qc_short_duration"])
    assert by_id.loc["short_duration", "qc_reasons"] == "qc_short_duration"
    assert bool(by_id.loc["outlier_rate", "qc_outlier_rate"])
    assert by_id.loc["outlier_rate", "qc_reasons"] == "qc_outlier_rate"
    assert by_id.loc["two_reasons", "qc_status"] == "fail"
    assert by_id.loc["two_reasons", "qc_reasons"] == "qc_low_active_channels,qc_short_duration"


def test_compute_qc_flags_honors_custom_thresholds() -> None:
    manifest = pd.DataFrame(
        {
            "recording_id": ["rec1"],
            "condition": ["control"],
            "active_channel_count": [5],
            "recording_duration_s": [80.0],
            "mean_firing_rate_hz": [1.0],
        }
    )

    result = compute_qc_flags(
        manifest,
        thresholds=QCThresholds(min_active_channels=6, min_duration_s=90.0),
    )

    assert result.loc[0, "qc_status"] == "fail"
    assert result.loc[0, "qc_reasons"] == "qc_low_active_channels,qc_short_duration"
