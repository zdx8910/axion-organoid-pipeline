"""Workflow F (Fig. 6): condition and group comparison plots."""

from collections.abc import Sequence
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


def _significance_label(p_value: float) -> str:
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""


def _add_significance(
    axis: Axes,
    *,
    stats: pd.DataFrame,
    metric: str,
    order: Sequence[str],
    y_max: float,
) -> None:
    metric_stats = stats.loc[(stats["metric"] == metric) & (stats["significant"])]
    if metric_stats.empty:
        return
    step = y_max * 0.08 if y_max != 0 else 1.0
    y = y_max + step
    positions = {group: index for index, group in enumerate(order)}
    for _, row in metric_stats.iterrows():
        group_a = str(row["group_a"])
        group_b = str(row["group_b"])
        if group_a not in positions or group_b not in positions:
            continue
        x1 = positions[group_a]
        x2 = positions[group_b]
        axis.plot([x1, x1, x2, x2], [y, y + step * 0.2, y + step * 0.2, y], color="black")
        axis.text(
            (x1 + x2) / 2,
            y + step * 0.22,
            _significance_label(float(row["p_adj"])),
            ha="center",
            va="bottom",
        )
        y += step


def plot_group_comparison(
    well_summary: pd.DataFrame,
    *,
    group_col: str,
    metric: str,
    order: Sequence[str] | None = None,
    palette: str = "deep",
    stats: pd.DataFrame | None = None,
    figsize: tuple[float, float] = (6.0, 5.0),
    ax: Axes | None = None,
) -> Figure:
    """Render a MEA-NAP-style half-violin plus dot plot.

    Parameters
    ----------
    well_summary
        Summary table containing the grouping column and metric.
    group_col
        Column containing group labels.
    metric
        Numeric metric to plot.
    order
        Optional group order.
    palette
        Seaborn palette name.
    stats
        Optional output from :func:`meaorganoid.compare.group.compare_groups` for annotations.
    figsize
        Figure size used when ``ax`` is not supplied.
    ax
        Optional axes to draw into.

    Returns
    -------
    matplotlib.figure.Figure
        Rendered comparison figure.

    Examples
    --------
    >>> frame = pd.DataFrame({"group": ["a", "a", "b", "b"], "value": [1.0, 1.1, 2.0, 2.1]})
    >>> fig = plot_group_comparison(frame, group_col="group", metric="value")
    >>> len(fig.axes)
    1
    >>> plt.close(fig)

    Notes
    -----
    This function draws full seaborn violins and clips each violin artist to the left half of its
    group slot, then places jittered observations on the right half.
    """
    if order is None:
        order = [str(group) for group in sorted(well_summary[group_col].dropna().unique())]
    frame = well_summary.copy()
    frame[group_col] = frame[group_col].astype(str)
    figure: Figure
    if ax is None:
        figure, axis = plt.subplots(figsize=figsize)
    else:
        axis = ax
        figure = cast(Figure, axis.figure)

    sns.violinplot(
        data=frame,
        x=group_col,
        y=metric,
        hue=group_col,
        order=list(order),
        hue_order=list(order),
        palette=palette,
        inner=None,
        cut=0,
        linewidth=1.0,
        legend=False,
        ax=axis,
    )
    y_min, y_max = axis.get_ylim()
    for index, collection in enumerate(axis.collections[: len(order)]):
        clip = Rectangle((index - 0.5, y_min), 0.5, y_max - y_min, transform=axis.transData)
        collection.set_clip_path(clip)

    rng = np.random.default_rng(0)
    palette_values = sns.color_palette(palette, n_colors=len(order))
    for index, group in enumerate(order):
        values = frame.loc[frame[group_col] == group, metric].dropna().to_numpy(dtype=float)
        jitter = rng.uniform(0.05, 0.35, size=values.size)
        axis.scatter(
            np.full(values.size, index, dtype=float) + jitter,
            values,
            s=24,
            alpha=0.8,
            color=palette_values[index],
            edgecolor="black",
            linewidth=0.4,
            zorder=3,
        )
        if values.size:
            median = float(np.median(values))
            axis.plot([index - 0.35, index + 0.35], [median, median], color="black", linewidth=1.4)

    if stats is not None:
        _add_significance(
            axis,
            stats=stats,
            metric=metric,
            order=order,
            y_max=float(frame[metric].max()),
        )

    axis.set_title(metric)
    axis.set_ylabel(metric)
    axis.set_xlabel(group_col)
    figure.tight_layout()
    return figure
