from pathlib import Path

import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.integration
def test_plot_raster_cli_writes_one_png_per_well(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "raster"

    result = runner.invoke(
        main,
        [
            "plot-raster",
            "--input",
            str(FIXTURE_DIR / "raster_events.csv"),
            "--bursts-input",
            str(FIXTURE_DIR / "raster_bursts.csv"),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "fixture",
        ],
    )

    assert result.exit_code == 0, result.output
    outputs = sorted(output_dir.glob("fixture_raster_*.png"))
    assert [path.name for path in outputs] == ["fixture_raster_A1.png", "fixture_raster_A2.png"]
    assert all(path.stat().st_size > 0 for path in outputs)
