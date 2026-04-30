from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner

from meaorganoid.cli import main

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.integration
def test_connectivity_cli_writes_png_and_npz_per_well(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "connectivity"

    result = runner.invoke(
        main,
        [
            "connectivity",
            "--input",
            str(FIXTURE_DIR / "connectivity_events.csv"),
            "--channel-summary",
            str(FIXTURE_DIR / "connectivity_channel_summary.csv"),
            "--manifest",
            str(FIXTURE_DIR / "connectivity_manifest.csv"),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "fixture",
            "--n-iterations",
            "8",
            "--min-spikes",
            "10",
        ],
    )

    assert result.exit_code == 0, result.output
    for well in ["A1", "B2"]:
        figure_path = output_dir / f"fixture_connectivity_{well}.png"
        matrix_path = output_dir / f"fixture_connectivity_{well}.npz"
        assert figure_path.exists()
        assert figure_path.stat().st_size > 0
        assert matrix_path.exists()
        assert matrix_path.stat().st_size > 0
        with np.load(matrix_path, allow_pickle=True) as data:
            adjacency = data["adjacency"]
            assert np.allclose(adjacency, adjacency.T, equal_nan=True)
            assert np.allclose(np.diag(adjacency), 1.0)
            assert set(data.files) == {
                "adjacency",
                "significance_mask",
                "electrode_labels",
                "params",
            }
