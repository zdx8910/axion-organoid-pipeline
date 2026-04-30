from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.integration
def test_workflow_c_compare_baseline_and_conditions_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "compare"
    input_path = FIXTURE_DIR / "well_summary_paired.csv"

    baseline_result = runner.invoke(
        main,
        [
            "compare-baseline",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "paired",
            "--baseline-label",
            "baseline",
        ],
    )
    assert baseline_result.exit_code == 0, baseline_result.output

    stats_result = runner.invoke(
        main,
        [
            "compare-conditions",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "paired",
            "--condition-a",
            "baseline",
            "--condition-b",
            "treatment",
        ],
    )
    assert stats_result.exit_code == 0, stats_result.output

    delta_path = output_dir / "paired_well_delta_from_baseline.csv"
    stats_path = output_dir / "paired_paired_condition_stats.csv"
    assert delta_path.exists()
    assert stats_path.exists()

    assert pd.read_csv(delta_path, nrows=0).columns.tolist() == [
        "well",
        "condition",
        "mean_firing_rate_hz",
        "active_channel_count",
        "mean_firing_rate_hz__delta",
        "mean_firing_rate_hz__pct_change",
        "active_channel_count__delta",
        "active_channel_count__pct_change",
    ]
    assert pd.read_csv(stats_path, nrows=0).columns.tolist() == [
        "metric",
        "n_pairs",
        "mean_a",
        "mean_b",
        "mean_diff",
        "ci_low",
        "ci_high",
        "wilcoxon_W",
        "wilcoxon_p",
        "p_holm",
        "significant",
    ]
