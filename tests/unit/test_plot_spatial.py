import matplotlib.pyplot as plt
import pandas as pd
import pytest

from meaorganoid.errors import MEASchemaError, MEAValueError
from meaorganoid.plot.spatial import plot_spatial_heatmap


def _channel_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "well": ["A1", "A1", "A1", "A1"],
            "electrode": ["A1_11", "A1_12", "A1_21", "A1_22"],
            "mean_firing_rate_hz": [1.0, 2.0, 3.0, 4.0],
            "active": [True, False, True, True],
        }
    )


def test_plot_spatial_heatmap_has_expected_grid_cells() -> None:
    figure = plot_spatial_heatmap(_channel_summary(), well="A1", grid_shape=(4, 4))

    try:
        image = figure.axes[0].images[0]
        assert image.get_array().shape == (4, 4)
    finally:
        plt.close(figure)


def test_plot_spatial_heatmap_hatches_inactive_electrodes() -> None:
    figure = plot_spatial_heatmap(_channel_summary(), well="A1")

    try:
        hatches = [patch.get_hatch() for patch in figure.axes[0].patches]
        assert "////" in hatches
    finally:
        plt.close(figure)


def test_plot_spatial_heatmap_missing_metric_raises() -> None:
    with pytest.raises(MEAValueError, match="missing"):
        plot_spatial_heatmap(_channel_summary(), well="A1", metric="missing")


def test_plot_spatial_heatmap_invalid_electrode_label_raises_schema_error() -> None:
    frame = _channel_summary()
    frame.loc[0, "electrode"] = "not_an_electrode"

    with pytest.raises(MEASchemaError, match="not_an_electrode"):
        plot_spatial_heatmap(frame, well="A1")


def test_plot_spatial_heatmap_honors_vmin_vmax() -> None:
    figure = plot_spatial_heatmap(_channel_summary(), well="A1", vmin=0.0, vmax=10.0)

    try:
        image = figure.axes[0].images[0]
        assert image.norm.vmin == pytest.approx(0.0)
        assert image.norm.vmax == pytest.approx(10.0)
    finally:
        plt.close(figure)


def test_plot_spatial_heatmap_global_scale_can_match_across_wells() -> None:
    frame = pd.DataFrame(
        {
            "well": ["A1", "A1", "B2", "B2"],
            "electrode": ["A1_11", "A1_12", "B2_11", "B2_12"],
            "mean_firing_rate_hz": [1.0, 2.0, 9.0, 10.0],
            "active": [True, True, True, True],
        }
    )
    vmin = float(frame["mean_firing_rate_hz"].min())
    vmax = float(frame["mean_firing_rate_hz"].max())
    figure_a = plot_spatial_heatmap(frame, well="A1", vmin=vmin, vmax=vmax)
    figure_b = plot_spatial_heatmap(frame, well="B2", vmin=vmin, vmax=vmax)

    try:
        assert figure_a.axes[0].images[0].norm.vmin == figure_b.axes[0].images[0].norm.vmin
        assert figure_a.axes[0].images[0].norm.vmax == figure_b.axes[0].images[0].norm.vmax
    finally:
        plt.close(figure_a)
        plt.close(figure_b)
