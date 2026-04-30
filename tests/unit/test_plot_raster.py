import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.figure import Figure

from meaorganoid.errors import MEAValueError
from meaorganoid.plot.raster import plot_raster


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_s": [0.0, 0.2, 0.4, 0.6, 0.1, 0.3, 0.5, 0.7],
            "electrode": ["A1_1", "A1_10", "A1_2", "A1_2", "A2_1", "A2_1", "A2_2", "A2_2"],
            "well": ["A1", "A1", "A1", "A1", "A2", "A2", "A2", "A2"],
        }
    )


def test_plot_raster_returns_figure_with_two_axes() -> None:
    figure = plot_raster(_events(), well="A1")

    try:
        assert isinstance(figure, Figure)
        assert len(figure.axes) >= 2
    finally:
        plt.close(figure)


def test_plot_raster_missing_well_raises() -> None:
    with pytest.raises(MEAValueError, match="missing"):
        plot_raster(_events(), well="missing")


def test_plot_raster_uses_natural_electrode_sort() -> None:
    figure = plot_raster(_events(), well="A1")

    try:
        labels = [label.get_text() for label in figure.axes[0].get_yticklabels()]
        assert labels == ["A1_1", "A1_2", "A1_10"]
    finally:
        plt.close(figure)


def test_plot_raster_adds_burst_patches() -> None:
    bursts = pd.DataFrame(
        {
            "well": ["A1"],
            "electrode": ["A1_1"],
            "start_s": [0.0],
            "end_s": [0.2],
        }
    )

    figure = plot_raster(_events(), well="A1", bursts=bursts)

    try:
        assert len(figure.axes[0].patches) >= 1
    finally:
        plt.close(figure)
