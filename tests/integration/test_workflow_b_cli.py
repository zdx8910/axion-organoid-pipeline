from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"

BURSTS_COLUMNS = [
    "well",
    "electrode",
    "burst_index",
    "start_s",
    "end_s",
    "duration_s",
    "n_spikes",
    "mean_isi_s",
    "intra_burst_rate_hz",
    "method",
]
SUMMARY_COLUMNS = [
    "well",
    "electrode",
    "n_bursts",
    "mean_burst_duration_s",
    "mean_intra_burst_rate_hz",
    "mean_ibi_s",
    "burst_rate_hz",
    "percent_spikes_in_bursts",
]


@pytest.mark.integration
def test_workflow_b_bursts_cli_writes_public_outputs(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "bursts"

    result = runner.invoke(
        main,
        [
            "bursts",
            "--input",
            str(FIXTURE_DIR / "burst_events.csv"),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "fixture",
            "--method",
            "maxinterval",
        ],
    )

    assert result.exit_code == 0, result.output
    bursts_path = output_dir / "fixture_bursts.csv"
    summary_path = output_dir / "fixture_burst_summary.csv"
    assert bursts_path.exists()
    assert summary_path.exists()

    bursts = pd.read_csv(bursts_path)
    summary = pd.read_csv(summary_path)
    assert bursts.columns.tolist() == BURSTS_COLUMNS
    assert summary.columns.tolist() == SUMMARY_COLUMNS

    burst_counts = bursts.groupby(["well", "electrode"])["burst_index"].nunique()
    summary_counts = summary.set_index(["well", "electrode"])["n_bursts"]
    assert summary_counts.sort_index().tolist() == burst_counts.sort_index().tolist()
