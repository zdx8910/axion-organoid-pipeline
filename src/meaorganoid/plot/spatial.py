"""Workflow E (Fig. 5): spatial firing heatmaps."""

import re
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from meaorganoid.errors import MEASchemaError, MEAValueError

_ELECTRODE_RE = re.compile(r"^(?P<well>.+)_(?P<row>\d)(?P<col>\d)$")


def _active_column(frame: pd.DataFrame) -> str | None:
    for column in ("active", "is_active"):
        if column in frame.columns:
            return column
    return None


def _parse_coordinates(
    frame: pd.DataFrame, *, well: str, grid_shape: tuple[int, int]
) -> pd.DataFrame:
    rows = []
    invalid: list[str] = []
    max_row, max_col = grid_shape
    for electrode in frame["electrode"].astype(str):
        match = _ELECTRODE_RE.match(electrode)
        if match is None or match.group("well") != well:
            invalid.append(electrode)
            continue
        row = int(match.group("row"))
        col = int(match.group("col"))
        if row < 1 or row > max_row or col < 1 or col > max_col:
            invalid.append(electrode)
            continue
        rows.append({"electrode": electrode, "row": row - 1, "col": col - 1})
    if invalid:
        raise MEASchemaError(f"channel_summary: invalid electrode label(s) {sorted(set(invalid))}")
    return pd.DataFrame(rows)


def plot_spatial_heatmap(
    channel_summary: pd.DataFrame,
    *,
    well: str,
    metric: str = "mean_firing_rate_hz",
    grid_shape: tuple[int, int] = (4, 4),
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
    annotate: bool = True,
    ax: Axes | None = None,
) -> Figure:
    """Render a spatial electrode heatmap for one well.

    Parameters
    ----------
    channel_summary
        Per-channel summary table with ``well``, ``electrode``, and metric columns.
    well
        Well label to render.
    metric
        Numeric column to place on the electrode grid.
    grid_shape
        Number of grid rows and columns.
    cmap
        Matplotlib colormap name.
    vmin
        Optional lower color scale bound.
    vmax
        Optional upper color scale bound.
    annotate
        Whether to write metric values in cells.
    ax
        Optional axes to draw into.

    Returns
    -------
    matplotlib.figure.Figure
        Rendered spatial heatmap figure.

    Examples
    --------
    >>> frame = pd.DataFrame(
    ...     {"well": ["A1"], "electrode": ["A1_11"], "mean_firing_rate_hz": [1.0], "active": [True]}
    ... )
    >>> fig = plot_spatial_heatmap(frame, well="A1")
    >>> len(fig.axes) >= 2
    True
    >>> plt.close(fig)
    """
    required = {"well", "electrode", metric}
    missing = sorted(required.difference(channel_summary.columns))
    if missing:
        raise MEAValueError(f"channel_summary: missing required column(s) {missing}")

    well_summary = channel_summary.loc[channel_summary["well"].astype(str) == well].copy()
    if well_summary.empty:
        raise MEAValueError(f"channel_summary: well {well!r} has no electrodes")

    coords = _parse_coordinates(well_summary, well=well, grid_shape=grid_shape)
    merged = well_summary.merge(coords, on="electrode", how="inner", validate="one_to_one")
    values = np.full(grid_shape, np.nan, dtype=float)
    active = np.ones(grid_shape, dtype=bool)
    active_column = _active_column(merged)

    for _, row in merged.iterrows():
        row_index = int(row["row"])
        col_index = int(row["col"])
        values[row_index, col_index] = float(row[metric])
        if active_column is not None:
            active[row_index, col_index] = bool(row[active_column])

    masked = np.ma.masked_invalid(values)
    colormap = plt.get_cmap(cmap).copy()
    colormap.set_bad(alpha=0)
    if ax is None:
        figure, axis = plt.subplots(figsize=(5, 4))
    else:
        axis = ax
        figure = cast(Figure, axis.figure)
    image = axis.imshow(masked, cmap=colormap, vmin=vmin, vmax=vmax)

    for row_index in range(grid_shape[0]):
        for col_index in range(grid_shape[1]):
            if not np.isnan(values[row_index, col_index]) and annotate:
                axis.text(
                    col_index,
                    row_index,
                    f"{values[row_index, col_index]:.3g}",
                    ha="center",
                    va="center",
                    color="white" if values[row_index, col_index] > np.nanmean(values) else "black",
                )
            if not active[row_index, col_index] and not np.isnan(values[row_index, col_index]):
                axis.add_patch(
                    Rectangle(
                        (col_index - 0.5, row_index - 0.5),
                        1.0,
                        1.0,
                        fill=False,
                        hatch="////",
                        edgecolor="black",
                        linewidth=0.0,
                    )
                )

    axis.set_xticks(
        range(grid_shape[1]), labels=[str(index) for index in range(1, grid_shape[1] + 1)]
    )
    axis.set_yticks(
        range(grid_shape[0]), labels=[str(index) for index in range(1, grid_shape[0] + 1)]
    )
    axis.set_xlabel("Electrode column")
    axis.set_ylabel("Electrode row")
    axis.set_title(f"{well} — {metric}")
    axis.set_xlim(-0.5, grid_shape[1] - 0.5)
    axis.set_ylim(grid_shape[0] - 0.5, -0.5)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label(metric)
    figure.tight_layout()
    return figure
