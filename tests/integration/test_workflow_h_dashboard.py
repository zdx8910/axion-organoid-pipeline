from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.integration
def test_qc_report_cli_writes_dashboard_and_summary(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "qc"

    result = runner.invoke(
        main,
        [
            "qc-report",
            "--input",
            str(FIXTURE_DIR / "recording_manifest_small.csv"),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output

    dashboard = output_dir / "recording_manifest_small_qc_dashboard.png"
    summary = output_dir / "recording_manifest_small_qc_summary.csv"
    assert dashboard.exists()
    assert dashboard.stat().st_size > 0
    assert summary.exists()
    assert pd.read_csv(summary, nrows=0).columns.tolist() == [
        "qc_reason",
        "count",
        "percentage",
    ]
