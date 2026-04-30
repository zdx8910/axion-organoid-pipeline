from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from meaorganoid.cli import main
from meaorganoid.compare.group import GROUP_COMPARISON_COLUMNS

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.integration
def test_compare_group_cli_writes_stats_and_figures(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "group"

    result = runner.invoke(
        main,
        [
            "compare-group",
            "--input",
            str(FIXTURE_DIR / "well_summary_groups.csv"),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "groups",
            "--group-col",
            "group",
            "--metrics",
            "mean_firing_rate_hz,active_channel_count,burst_rate_hz",
        ],
    )

    assert result.exit_code == 0, result.output
    stats_path = output_dir / "groups_group_comparison.csv"
    assert stats_path.exists()
    stats = pd.read_csv(stats_path)
    assert list(stats.columns) == list(GROUP_COMPARISON_COLUMNS)
    assert len(stats) == 9
    assert stats.loc[stats["metric"] == "mean_firing_rate_hz", "p_adj"].min() < 0.05
    for metric in ["mean_firing_rate_hz", "active_channel_count", "burst_rate_hz"]:
        figure_path = output_dir / f"groups_group_comparison_{metric}.png"
        assert figure_path.exists()
        assert figure_path.stat().st_size > 0
