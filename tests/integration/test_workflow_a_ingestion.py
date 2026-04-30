import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def _sorted_columns(path: Path) -> list[str]:
    return sorted(pd.read_csv(path, nrows=0).columns.tolist())


@pytest.mark.integration
def test_workflow_a_process_cli_writes_expected_outputs(tmp_path: Path) -> None:
    runner = CliRunner()
    prefix = "workflow_a"
    output_dir = tmp_path / "out"

    result = runner.invoke(
        main,
        [
            "process",
            "--input",
            str(FIXTURE_DIR / "axion_with_well.csv"),
            "--output-dir",
            str(output_dir),
            "--prefix",
            prefix,
        ],
    )

    assert result.exit_code == 0, result.output

    well_summary = output_dir / f"{prefix}_well_summary.csv"
    channel_summary = output_dir / f"{prefix}_channel_summary.csv"
    run_metadata = output_dir / f"{prefix}_run_metadata.json"
    input_metadata = output_dir / f"{prefix}_input_metadata.json"

    for path in (well_summary, channel_summary, run_metadata, input_metadata):
        assert path.exists()

    assert _sorted_columns(well_summary) == [
        "active_channel_count",
        "channel_count",
        "mean_firing_rate_hz",
        "median_firing_rate_hz",
        "qc_low_active_channels",
        "qc_outlier_rate",
        "qc_reasons",
        "qc_short_duration",
        "qc_status",
        "recording_duration_s",
        "total_spike_count",
        "well",
    ]
    assert _sorted_columns(channel_summary) == [
        "electrode",
        "firing_rate_hz",
        "is_active",
        "isi_mean_s",
        "isi_median_s",
        "recording_duration_s",
        "spike_count",
        "well",
    ]

    metadata: dict[str, Any] = json.loads(run_metadata.read_text(encoding="utf-8"))
    assert metadata["total_spike_count"] == pytest.approx(30)
