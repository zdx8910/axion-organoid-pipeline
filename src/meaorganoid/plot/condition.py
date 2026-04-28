"""Workflow F (Fig. 6): condition and group comparison plots."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_group_comparison(
    data: pd.DataFrame,
    value_column: str,
    group_column: str,
    output: str | Path,
) -> Path:
    """Write a simple group-comparison boxplot.

    Parameters
    ----------
    data
        Tidy table containing group labels and numeric values.
    value_column
        Numeric value column to plot.
    group_column
        Column containing group labels.
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
    data.boxplot(column=value_column, by=group_column, ax=axis)
    figure.suptitle("")
    axis.set_title(value_column)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path
