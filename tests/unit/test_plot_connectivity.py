import numpy as np
import pandas as pd

from meaorganoid.connectivity.plot import plot_connectivity_network


def test_plot_connectivity_network_returns_figure() -> None:
    summary = pd.DataFrame(
        {
            "well": ["A1", "A1"],
            "electrode": ["A1_11", "A1_12"],
            "mean_firing_rate_hz": [1.0, 2.0],
        }
    )

    figure = plot_connectivity_network(
        np.array([[1.0, 0.8], [0.8, 1.0]]),
        ["A1_11", "A1_12"],
        channel_summary=summary,
    )

    assert len(figure.axes) >= 2
    figure.clear()
