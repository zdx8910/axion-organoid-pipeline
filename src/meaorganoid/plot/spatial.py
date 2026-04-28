"""Workflow E (Fig. 5): spatial firing heatmaps."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_spatial_heatmap(summary: pd.DataFrame, output: str | Path) -> Path:
    """Write a basic spatial firing-rate heatmap.

    Parameters
    ----------
    summary
        Table containing ``electrode`` and ``firing_rate_hz`` columns.
    output
        Output figure path.

    Returns
    -------
    pathlib.Path
        Written output path.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    output_path = Path(output)
    figure, axis = plt.subplots(figsize=(6, 4))
    summary.plot.bar(x="electrode", y="firing_rate_hz", ax=axis, legend=False)
    axis.set_ylabel("Firing rate (Hz)")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path
