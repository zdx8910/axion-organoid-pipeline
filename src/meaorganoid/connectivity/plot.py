"""Workflow G (Fig. 7): connectivity network plots."""

from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from meaorganoid.errors import MEAValueError
from meaorganoid.plot.spatial import _parse_coordinates


def plot_connectivity_network(
    adjacency: np.ndarray,
    electrode_labels: list[str],
    *,
    channel_summary: pd.DataFrame,
    grid_shape: tuple[int, int] = (4, 4),
    edge_threshold: float = 0.0,
    node_metric: str = "mean_firing_rate_hz",
    node_cmap: str = "viridis",
    edge_alpha_scale: bool = True,
    title: str | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot an STTC connectivity network on the well electrode grid.

    Parameters
    ----------
    adjacency
        Square STTC adjacency matrix.
    electrode_labels
        Electrode labels matching matrix order.
    channel_summary
        Per-channel summary table containing ``well``, ``electrode``, and ``node_metric``.
    grid_shape
        Number of electrode rows and columns.
    edge_threshold
        Skip edges with absolute weight at or below this threshold.
    node_metric
        Channel summary column used for node color and size.
    node_cmap
        Matplotlib colormap name for nodes.
    edge_alpha_scale
        Whether edge alpha scales with edge weight magnitude.
    title
        Optional figure title.
    ax
        Optional axes to draw into.

    Returns
    -------
    matplotlib.figure.Figure
        Rendered connectivity network.

    Examples
    --------
    >>> summary = pd.DataFrame(
    ...     {
    ...         "well": ["A1", "A1"],
    ...         "electrode": ["A1_11", "A1_12"],
    ...         "mean_firing_rate_hz": [1.0, 2.0],
    ...     }
    ... )
    >>> fig = plot_connectivity_network(np.eye(2), ["A1_11", "A1_12"], channel_summary=summary)
    >>> len(fig.axes) >= 1
    True
    >>> plt.close(fig)
    """
    matrix = np.asarray(adjacency, dtype=float)
    if matrix.shape != (len(electrode_labels), len(electrode_labels)):
        raise MEAValueError("adjacency: shape must match electrode_labels length")
    missing = sorted({"well", "electrode", node_metric}.difference(channel_summary.columns))
    if missing:
        raise MEAValueError(f"channel_summary: missing required column(s) {missing}")

    if ax is None:
        figure, axis = plt.subplots(figsize=(6, 5))
    else:
        axis = ax
        figure = cast(Figure, axis.figure)

    if not electrode_labels:
        axis.set_axis_off()
        axis.set_title(title or "Connectivity")
        return figure

    well = str(electrode_labels[0]).rsplit("_", maxsplit=1)[0]
    node_summary = channel_summary.loc[
        channel_summary["electrode"].astype(str).isin(electrode_labels)
    ].copy()
    coords = _parse_coordinates(node_summary, well=well, grid_shape=grid_shape)
    merged = node_summary.merge(coords, on="electrode", how="inner", validate="one_to_one")
    metric_by_electrode = {
        str(row["electrode"]): float(row[node_metric]) for _, row in merged.iterrows()
    }
    coord_by_electrode = {
        str(row["electrode"]): (float(row["col"]), float(row["row"]))
        for _, row in merged.iterrows()
    }

    weights = np.abs(matrix[np.triu_indices_from(matrix, k=1)])
    finite_weights = weights[np.isfinite(weights)]
    max_weight = float(finite_weights.max()) if finite_weights.size else 1.0

    for left in range(len(electrode_labels)):
        for right in range(left + 1, len(electrode_labels)):
            value = matrix[left, right]
            if not np.isfinite(value) or abs(value) <= edge_threshold:
                continue
            left_label = electrode_labels[left]
            right_label = electrode_labels[right]
            if left_label not in coord_by_electrode or right_label not in coord_by_electrode:
                continue
            x_left, y_left = coord_by_electrode[left_label]
            x_right, y_right = coord_by_electrode[right_label]
            scaled = abs(float(value)) / max(max_weight, 1e-12)
            axis.plot(
                [x_left, x_right],
                [y_left, y_right],
                color="#2f2f2f",
                linewidth=0.6 + 3.0 * scaled,
                alpha=0.2 + 0.7 * scaled if edge_alpha_scale else 0.7,
                zorder=1,
            )

    values = np.array([metric_by_electrode[label] for label in electrode_labels], dtype=float)
    sizes = 80.0 + 180.0 * (values / max(float(np.nanmax(values)), 1e-12))
    xs = [coord_by_electrode[label][0] for label in electrode_labels]
    ys = [coord_by_electrode[label][1] for label in electrode_labels]
    scatter = axis.scatter(
        xs,
        ys,
        c=values,
        s=sizes,
        cmap=node_cmap,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )
    for label, x, y in zip(electrode_labels, xs, ys, strict=True):
        axis.text(x, y, label.rsplit("_", maxsplit=1)[-1], ha="center", va="center", fontsize=8)

    colorbar = figure.colorbar(scatter, ax=axis)
    colorbar.set_label(node_metric)
    legend_handles = [
        Line2D([0], [0], color="#2f2f2f", linewidth=0.6 + 3.0 * value, label=f"{value:.1f}")
        for value in (0.25, 0.5, 1.0)
    ]
    axis.legend(handles=legend_handles, title="|STTC|", loc="upper right", frameon=True)
    axis.set_xticks(
        range(grid_shape[1]), labels=[str(index) for index in range(1, grid_shape[1] + 1)]
    )
    axis.set_yticks(
        range(grid_shape[0]), labels=[str(index) for index in range(1, grid_shape[0] + 1)]
    )
    axis.set_xlim(-0.5, grid_shape[1] - 0.5)
    axis.set_ylim(grid_shape[0] - 0.5, -0.5)
    axis.set_xlabel("Electrode column")
    axis.set_ylabel("Electrode row")
    axis.set_title(title or f"{well} connectivity")
    axis.set_aspect("equal")
    figure.tight_layout()
    return figure
