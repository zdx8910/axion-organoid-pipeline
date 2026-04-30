"""Workflow D (Fig. 4): NMT-style raster plotting."""

import re
from collections.abc import Iterable
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from meaorganoid.errors import MEAValueError


def _natural_key(label: object) -> tuple[object, ...]:
    parts = re.split(r"(\d+)", str(label))
    return tuple(int(part) if part.isdigit() else part.casefold() for part in parts)


def _natural_sort(labels: Iterable[object]) -> list[str]:
    return sorted((str(label) for label in labels), key=_natural_key)


def _validate_events(events: pd.DataFrame) -> None:
    missing = sorted({"time_s", "electrode", "well"}.difference(events.columns))
    if missing:
        raise MEAValueError(f"events: missing required column(s) {missing}")


def _filter_time_window(
    frame: pd.DataFrame,
    time_window_s: tuple[float, float] | None,
) -> pd.DataFrame:
    if time_window_s is None:
        return cast(pd.DataFrame, frame.copy())
    start_s, end_s = time_window_s
    return cast(
        pd.DataFrame,
        frame.loc[(frame["time_s"] >= start_s) & (frame["time_s"] <= end_s)].copy(),
    )


def _time_limits(
    well_events: pd.DataFrame,
    time_window_s: tuple[float, float] | None,
) -> tuple[float, float]:
    if time_window_s is not None:
        return time_window_s
    if well_events.empty:
        return 0.0, 1.0
    start = float(well_events["time_s"].min())
    end = float(well_events["time_s"].max())
    if start == end:
        end = start + 1.0
    return start, end


def _create_axes(
    *,
    figsize: tuple[float, float],
    ax: Axes | None,
) -> tuple[Figure, Axes, Axes]:
    if ax is not None:
        figure = cast(Figure, ax.figure)
        bottom = figure.add_subplot(2, 1, 2, sharex=ax)
        return figure, ax, bottom
    figure, (raster_ax, rate_ax) = plt.subplots(
        2,
        1,
        figsize=figsize,
        height_ratios=[4, 1],
        sharex=True,
    )
    return figure, raster_ax, rate_ax


def plot_raster(
    events: pd.DataFrame,
    *,
    well: str,
    time_window_s: tuple[float, float] | None = None,
    bursts: pd.DataFrame | None = None,
    firing_rate_bin_s: float = 1.0,
    title: str | None = None,
    figsize: tuple[float, float] = (10.0, 6.0),
    ax: Axes | None = None,
) -> Figure:
    """Render an NMT-style raster plot for one well.

    Parameters
    ----------
    events
        Canonical Workflow A spike events with ``time_s``, ``electrode``, and ``well`` columns.
    well
        Well label to render.
    time_window_s
        Optional inclusive x-axis window in seconds.
    bursts
        Optional Workflow B burst table used for translucent burst overlays.
    firing_rate_bin_s
        Bin width in seconds for the population firing-rate trace.
    title
        Optional figure title. Defaults to ``"Raster — <well>"``.
    figsize
        Figure size used when ``ax`` is not provided.
    ax
        Optional top raster axes. A bottom firing-rate axes is still created and shared.

    Returns
    -------
    matplotlib.figure.Figure
        Rendered raster figure.

    Examples
    --------
    >>> events = pd.DataFrame(
    ...     {"time_s": [0.0, 0.1], "electrode": ["A1_1", "A1_2"], "well": ["A1", "A1"]}
    ... )
    >>> figure = plot_raster(events, well="A1")
    >>> len(figure.axes) >= 2
    True
    >>> plt.close(figure)
    """
    _validate_events(events)
    if firing_rate_bin_s <= 0:
        raise MEAValueError("firing_rate_bin_s: must be greater than 0")

    matching = events.loc[events["well"].astype(str) == well].copy()
    if matching.empty:
        raise MEAValueError(f"events: well {well!r} not found")
    well_events = _filter_time_window(matching, time_window_s)
    electrodes = _natural_sort(matching["electrode"].unique())
    y_positions = {electrode: index for index, electrode in enumerate(electrodes)}
    start_s, end_s = _time_limits(well_events, time_window_s)

    figure, raster_ax, rate_ax = _create_axes(figsize=figsize, ax=ax)
    for electrode in electrodes:
        spike_times = well_events.loc[
            well_events["electrode"].astype(str) == electrode, "time_s"
        ].to_numpy(dtype=float)
        if spike_times.size:
            raster_ax.vlines(
                spike_times,
                y_positions[electrode] - 0.35,
                y_positions[electrode] + 0.35,
                color="black",
                linewidth=0.8,
            )

    if bursts is not None and not bursts.empty:
        well_bursts = bursts.loc[bursts["well"].astype(str) == well].copy()
        if time_window_s is not None:
            well_bursts = well_bursts.loc[
                (well_bursts["end_s"] >= start_s) & (well_bursts["start_s"] <= end_s)
            ]
        for _, burst in well_bursts.iterrows():
            electrode = str(burst["electrode"])
            if electrode not in y_positions:
                continue
            burst_start = max(float(burst["start_s"]), start_s)
            burst_end = min(float(burst["end_s"]), end_s)
            raster_ax.add_patch(
                Rectangle(
                    (burst_start, y_positions[electrode] - 0.45),
                    burst_end - burst_start,
                    0.9,
                    facecolor="#d65f5f",
                    alpha=0.25,
                    edgecolor="none",
                )
            )

    bins = np.arange(start_s, end_s + firing_rate_bin_s, firing_rate_bin_s)
    if bins.size < 2:
        bins = np.array([start_s, start_s + firing_rate_bin_s])
    counts, edges = np.histogram(well_events["time_s"].to_numpy(dtype=float), bins=bins)
    centers = edges[:-1] + np.diff(edges) / 2.0
    rates = counts / firing_rate_bin_s
    rate_ax.plot(centers, rates, color="#2f6f9f", linewidth=1.5)

    raster_ax.set_yticks(list(y_positions.values()), labels=electrodes)
    raster_ax.set_ylim(-0.75, len(electrodes) - 0.25)
    raster_ax.set_xlim(start_s, end_s)
    raster_ax.set_ylabel("Electrode")
    raster_ax.set_title(title or f"Raster — {well}")
    rate_ax.set_xlabel("Time (s)")
    rate_ax.set_ylabel("Spikes/s")
    rate_ax.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    return figure
