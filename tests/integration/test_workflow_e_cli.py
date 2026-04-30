from pathlib import Path

import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.integration
def test_plot_spatial_cli_writes_one_png_per_well(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "spatial"

    result = runner.invoke(
        main,
        [
            "plot-spatial",
            "--input",
            str(FIXTURE_DIR / "channel_summary.csv"),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "fixture",
            "--global-scale",
        ],
    )

    assert result.exit_code == 0, result.output
    outputs = sorted(output_dir.glob("fixture_spatial_heatmap_*.png"))
    assert [path.name for path in outputs] == [
        "fixture_spatial_heatmap_A1.png",
        "fixture_spatial_heatmap_B2.png",
    ]
    assert all(path.stat().st_size > 0 for path in outputs)
