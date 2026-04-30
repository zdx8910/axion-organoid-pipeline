"""Click command-line interface for meaorganoid."""

import json
import logging
from pathlib import Path
from typing import Any, Literal, cast

import click
import pandas as pd

from meaorganoid.bursts import detect_bursts
from meaorganoid.compare import compute_paired_condition_stats, compute_well_delta
from meaorganoid.compare.group import DEFAULT_GROUP_METRICS, compare_groups
from meaorganoid.connectivity import compute_lag_window_adjacency
from meaorganoid.io import read_axion_spike_csv
from meaorganoid.metrics import compute_channel_summary, compute_well_summary
from meaorganoid.plot.condition import plot_group_comparison
from meaorganoid.plot.raster import plot_raster
from meaorganoid.plot.spatial import plot_spatial_heatmap
from meaorganoid.qc import add_qc_flags, compute_qc_flags, render_dashboard

LOGGER = logging.getLogger(__name__)
BURST_COLUMNS = [
    "well",
    "electrode",
    "burst_index",
    "start_s",
    "end_s",
    "duration_s",
    "n_spikes",
    "mean_isi_s",
    "intra_burst_rate_hz",
    "method",
]
BURST_SUMMARY_COLUMNS = [
    "well",
    "electrode",
    "n_bursts",
    "mean_burst_duration_s",
    "mean_intra_burst_rate_hz",
    "mean_ibi_s",
    "burst_rate_hz",
    "percent_spikes_in_bursts",
]
DEFAULT_COMPARE_METRICS = "mean_firing_rate_hz,active_channel_count"
DEFAULT_GROUP_METRICS_TEXT = ",".join(DEFAULT_GROUP_METRICS)


def _write_process_outputs(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    active_threshold_hz: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    spikes = read_axion_spike_csv(input_path)
    duration = float(spikes["time_s"].max() - spikes["time_s"].min()) if not spikes.empty else 0.0
    channel_summary = compute_channel_summary(
        spikes,
        recording_duration_s=duration if duration > 0 else None,
        active_threshold_hz=active_threshold_hz,
    )
    well_summary = add_qc_flags(compute_well_summary(channel_summary))

    channel_summary.to_csv(output_dir / f"{prefix}_channel_summary.csv", index=False)
    well_summary.to_csv(output_dir / f"{prefix}_well_summary.csv", index=False)
    (output_dir / f"{prefix}_run_metadata.json").write_text(
        json.dumps(
            {
                "input": str(input_path),
                "prefix": prefix,
                "total_spike_count": len(spikes),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / f"{prefix}_input_metadata.json").write_text(
        json.dumps(
            {
                "input": str(input_path),
                "columns": list(spikes.columns),
                "n_spikes": len(spikes),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _prefix_from_path(path: Path) -> str:
    return path.stem.replace(" ", "_")


def _configure_cli_logging() -> None:
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
        LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def _qc_summary(manifest: pd.DataFrame) -> pd.DataFrame:
    failing_reasons = manifest.loc[manifest["qc_reasons"] != "", "qc_reasons"]
    if failing_reasons.empty:
        return pd.DataFrame({"qc_reason": [], "count": [], "percentage": []})

    counts = failing_reasons.str.split(",").explode().value_counts().sort_values(ascending=False)
    summary = counts.rename_axis("qc_reason").reset_index(name="count")
    summary["percentage"] = summary["count"] / len(manifest) * 100.0
    return cast(pd.DataFrame, summary)


def _qc_prefix(path: Path) -> str:
    stem = path.stem
    suffix = "_recording_manifest"
    if stem.endswith(suffix):
        stem = stem[: -len(suffix)]
    return stem


def _read_events(path: Path) -> pd.DataFrame:
    if path.suffix.casefold() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _parse_metrics(metrics: str) -> list[str]:
    return [metric.strip() for metric in metrics.split(",") if metric.strip()]


def _parse_time_window(value: str | None) -> tuple[float, float] | None:
    if value is None:
        return None
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        raise click.BadParameter("expected '<start>,<end>'")
    start_s, end_s = float(parts[0]), float(parts[1])
    if end_s <= start_s:
        raise click.BadParameter("end must be greater than start")
    return start_s, end_s


def _burst_summary(events: pd.DataFrame, bursts: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for keys, group in events.groupby(["well", "electrode"], dropna=False):
        well, electrode = tuple(keys)
        group_bursts = bursts.loc[(bursts["well"] == well) & (bursts["electrode"] == electrode)]
        duration = float(group["time_s"].max() - group["time_s"].min()) if len(group) > 1 else 0.0
        if group_bursts.empty:
            mean_ibi = float("nan")
        else:
            sorted_bursts = group_bursts.sort_values("start_s")
            ibis = (
                sorted_bursts["start_s"].to_numpy(dtype=float)[1:]
                - sorted_bursts["end_s"].to_numpy(dtype=float)[:-1]
            )
            mean_ibi = float(ibis.mean()) if ibis.size else float("nan")
        spike_count_in_bursts = int(group_bursts["n_spikes"].sum()) if not group_bursts.empty else 0
        rows.append(
            {
                "well": well,
                "electrode": electrode,
                "n_bursts": len(group_bursts),
                "mean_burst_duration_s": float(group_bursts["duration_s"].mean())
                if not group_bursts.empty
                else float("nan"),
                "mean_intra_burst_rate_hz": float(group_bursts["intra_burst_rate_hz"].mean())
                if not group_bursts.empty
                else float("nan"),
                "mean_ibi_s": mean_ibi,
                "burst_rate_hz": float(len(group_bursts) / duration) if duration > 0 else 0.0,
                "percent_spikes_in_bursts": float(spike_count_in_bursts / len(group) * 100.0)
                if len(group) > 0
                else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=BURST_SUMMARY_COLUMNS)


@click.group()
def main() -> None:
    """Analyze Axion MEA spike CSV exports from brain organoid experiments."""


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", default=None, type=str)
@click.option("--active-threshold-hz", default=0.1, show_default=True, type=float)
def process(
    input_path: Path,
    output_dir: Path,
    prefix: str | None,
    active_threshold_hz: float,
) -> None:
    """Process one Axion spike CSV into summary tables."""
    _write_process_outputs(
        input_path, output_dir, prefix or _prefix_from_path(input_path), active_threshold_hz
    )


@main.command()
@click.option(
    "--input-dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--pattern", default="*.csv", show_default=True, type=str)
@click.option("--active-threshold-hz", default=0.1, show_default=True, type=float)
def batch(input_dir: Path, output_dir: Path, pattern: str, active_threshold_hz: float) -> None:
    """Process a directory of Axion spike CSVs."""
    run_batch(input_dir, output_dir, pattern, active_threshold_hz)


def run_batch(
    input_dir: Path,
    output_dir: Path,
    pattern: str,
    active_threshold_hz: float,
) -> None:
    """Run batch processing outside the Click command wrapper."""
    files = sorted(input_dir.glob(pattern))
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, str]] = []
    for input_path in files:
        prefix = _prefix_from_path(input_path)
        _write_process_outputs(input_path, output_dir, prefix, active_threshold_hz)
        manifest_rows.append({"input": str(input_path), "prefix": prefix})
    pd.DataFrame(manifest_rows).to_csv(output_dir / "batch_recording_manifest.csv", index=False)


@main.command()
@click.option(
    "--input-dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--output", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--pattern", default="*_well_summary.csv", show_default=True, type=str)
def aggregate(input_dir: Path, output: Path, pattern: str) -> None:
    """Aggregate well summary CSVs into one table."""
    run_aggregate(input_dir, output, pattern)


def run_aggregate(input_dir: Path, output: Path, pattern: str) -> None:
    """Run aggregation outside the Click command wrapper."""
    frames = []
    for path in sorted(input_dir.glob(pattern)):
        frame = pd.read_csv(path)
        frame["source_file"] = str(path)
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output, index=False)


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", default="summary", show_default=True, type=str)
def plot(input_path: Path, output_dir: Path, prefix: str) -> None:
    """Plot Axion summary CSVs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(input_path)
    first_well = (
        str(summary["well"].iloc[0])
        if "well" in summary.columns and not summary.empty
        else "unknown"
    )
    figure = plot_spatial_heatmap(summary, well=first_well)
    figure.savefig(output_dir / f"{prefix}_spatial_heatmap.png", dpi=150, bbox_inches="tight")
    figure.clear()


@main.command()
@click.option(
    "--input-dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--pattern", default="*_spike_list.csv", show_default=True, type=str)
@click.option("--combined-prefix", default="combined", show_default=True, type=str)
@click.option("--active-threshold-hz", default=0.1, show_default=True, type=float)
def pipeline(
    input_dir: Path,
    output_dir: Path,
    pattern: str,
    combined_prefix: str,
    active_threshold_hz: float,
) -> None:
    """Run batch processing and aggregate output tables."""
    run_batch(input_dir, output_dir, pattern, active_threshold_hz)
    run_aggregate(
        output_dir,
        output_dir / f"{combined_prefix}_well_summary.csv",
        "*_well_summary.csv",
    )


@main.command("compare-group")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", required=True, type=str)
@click.option("--group-col", default="group", show_default=True, type=str)
@click.option("--metrics", default=DEFAULT_GROUP_METRICS_TEXT, show_default=True, type=str)
@click.option(
    "--method",
    default="mannwhitneyu",
    show_default=True,
    type=click.Choice(["mannwhitneyu", "kruskal"]),
)
@click.option(
    "--correction",
    default="holm",
    show_default=True,
    type=click.Choice(["holm", "bh", "none"]),
)
@click.option("--min-n-per-group", default=3, show_default=True, type=int)
def compare_group(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    group_col: str,
    metrics: str,
    method: Literal["mannwhitneyu", "kruskal"],
    correction: Literal["holm", "bh", "none"],
    min_n_per_group: int,
) -> None:
    """Compute Workflow F MEA-NAP-style group statistics and plots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    well_summary = pd.read_csv(input_path)
    metric_list = _parse_metrics(metrics)
    stats_table = compare_groups(
        well_summary,
        group_col=group_col,
        metrics=metric_list,
        method=method,
        correction=correction,
        min_n_per_group=min_n_per_group,
    )
    stats_table.to_csv(output_dir / f"{prefix}_group_comparison.csv", index=False)
    for metric in metric_list:
        figure = plot_group_comparison(
            well_summary,
            group_col=group_col,
            metric=metric,
            stats=stats_table,
        )
        figure.savefig(
            output_dir / f"{prefix}_group_comparison_{metric}.png",
            dpi=150,
            bbox_inches="tight",
        )
        figure.clear()


@main.command("plot-group")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--value-column", required=True, type=str)
@click.option("--group-column", default="group", show_default=True, type=str)
@click.option("--prefix", default="group", show_default=True, type=str)
def plot_group(
    input_path: Path,
    output_dir: Path,
    value_column: str,
    group_column: str,
    prefix: str,
) -> None:
    """Plot a group comparison figure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    figure = plot_group_comparison(
        pd.read_csv(input_path),
        group_col=group_column,
        metric=value_column,
    )
    figure.savefig(output_dir / f"{prefix}_group_comparison.png", dpi=150, bbox_inches="tight")
    figure.clear()


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--lag-window-ms", default=50.0, show_default=True, type=float)
def connectivity(input_path: Path, output: Path, lag_window_ms: float) -> None:
    """Compute a lag-windowed connectivity adjacency matrix."""
    output.parent.mkdir(parents=True, exist_ok=True)
    adjacency = compute_lag_window_adjacency(
        read_axion_spike_csv(input_path),
        lag_window_ms / 1000.0,
    )
    adjacency.to_csv(output)


@main.command("qc-report")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option(
    "fmt",
    "--format",
    default="png",
    show_default=True,
    type=click.Choice(["png", "pdf"]),
)
def qc_report(input_path: Path, output_dir: Path, fmt: Literal["png", "pdf"]) -> None:
    """Render a Workflow H QC dashboard and summary table."""
    _configure_cli_logging()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = compute_qc_flags(pd.read_csv(input_path))
    prefix = _qc_prefix(input_path)
    dashboard_path = output_dir / f"{prefix}_qc_dashboard.{fmt}"
    summary_path = output_dir / f"{prefix}_qc_summary.csv"

    render_dashboard(manifest, dashboard_path, fmt=fmt)
    summary = _qc_summary(manifest)
    summary.to_csv(summary_path, index=False)

    pass_count = int((manifest["qc_status"] == "pass").sum())
    fail_count = int((manifest["qc_status"] == "fail").sum())
    top_reason = "none" if summary.empty else str(summary.iloc[0]["qc_reason"])
    LOGGER.info("QC pass count: %s", pass_count)
    LOGGER.info("QC fail count: %s", fail_count)
    LOGGER.info("Top failure reason: %s", top_reason)


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", required=True, type=str)
@click.option(
    "--method",
    default="maxinterval",
    show_default=True,
    type=click.Choice(["maxinterval", "logisi"]),
)
@click.option("--max-isi-start-s", default=0.170, show_default=True, type=float)
@click.option("--max-isi-end-s", default=0.300, show_default=True, type=float)
@click.option("--min-ibi-s", default=0.200, show_default=True, type=float)
@click.option("--min-burst-duration-s", default=0.010, show_default=True, type=float)
@click.option("--min-spikes-in-burst", default=3, show_default=True, type=int)
@click.option("--isi-threshold-s", default=None, type=float)
@click.option("--void-parameter", default=0.7, show_default=True, type=float)
def bursts(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    method: Literal["maxinterval", "logisi"],
    max_isi_start_s: float,
    max_isi_end_s: float,
    min_ibi_s: float,
    min_burst_duration_s: float,
    min_spikes_in_burst: int,
    isi_threshold_s: float | None,
    void_parameter: float,
) -> None:
    """Detect Workflow B ISI bursts from canonical events."""
    output_dir.mkdir(parents=True, exist_ok=True)
    events = _read_events(input_path)
    detector_kwargs: dict[str, Any] = {"min_spikes_in_burst": min_spikes_in_burst}
    if method == "maxinterval":
        detector_kwargs.update(
            {
                "max_isi_start_s": max_isi_start_s,
                "max_isi_end_s": max_isi_end_s,
                "min_ibi_s": min_ibi_s,
                "min_burst_duration_s": min_burst_duration_s,
            }
        )
    else:
        detector_kwargs.update(
            {
                "isi_threshold_s": isi_threshold_s,
                "void_parameter": void_parameter,
            }
        )

    burst_table = detect_bursts(events, method=method, **detector_kwargs)
    burst_table["method"] = method
    burst_table = burst_table.reindex(columns=BURST_COLUMNS)
    summary = _burst_summary(events, burst_table)
    burst_table.to_csv(output_dir / f"{prefix}_bursts.csv", index=False)
    summary.to_csv(output_dir / f"{prefix}_burst_summary.csv", index=False)


@main.command("compare-baseline")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", required=True, type=str)
@click.option("--baseline-label", required=True, type=str)
@click.option("--condition-col", default="condition", show_default=True, type=str)
@click.option("--metrics", default=DEFAULT_COMPARE_METRICS, show_default=True, type=str)
def compare_baseline(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    baseline_label: str,
    condition_col: str,
    metrics: str,
) -> None:
    """Compute Workflow C within-well deltas from baseline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    deltas = compute_well_delta(
        pd.read_csv(input_path),
        baseline_label=baseline_label,
        condition_col=condition_col,
        metrics=_parse_metrics(metrics),
    )
    deltas.to_csv(output_dir / f"{prefix}_well_delta_from_baseline.csv", index=False)


@main.command("compare-conditions")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", required=True, type=str)
@click.option("--condition-a", required=True, type=str)
@click.option("--condition-b", required=True, type=str)
@click.option("--condition-col", default="condition", show_default=True, type=str)
@click.option("--metrics", default=DEFAULT_COMPARE_METRICS, show_default=True, type=str)
def compare_conditions(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    condition_a: str,
    condition_b: str,
    condition_col: str,
    metrics: str,
) -> None:
    """Compute Workflow C paired condition statistics."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stats_table = compute_paired_condition_stats(
        pd.read_csv(input_path),
        condition_a=condition_a,
        condition_b=condition_b,
        condition_col=condition_col,
        metrics=_parse_metrics(metrics),
    )
    stats_table.to_csv(output_dir / f"{prefix}_paired_condition_stats.csv", index=False)


@main.command("plot-raster")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--bursts-input", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", required=True, type=str)
@click.option("--well", "wells", multiple=True, type=str)
@click.option("--time-window", default=None, type=str)
@click.option("--bin-s", default=1.0, show_default=True, type=float)
@click.option(
    "fmt",
    "--format",
    default="png",
    show_default=True,
    type=click.Choice(["png", "pdf", "svg"]),
)
@click.option("--dpi", default=150, show_default=True, type=int)
def plot_raster_command(
    input_path: Path,
    bursts_input: Path | None,
    output_dir: Path,
    prefix: str,
    wells: tuple[str, ...],
    time_window: str | None,
    bin_s: float,
    fmt: Literal["png", "pdf", "svg"],
    dpi: int,
) -> None:
    """Render Workflow D NMT-style raster plots."""
    _configure_cli_logging()
    output_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(input_path)
    bursts = pd.read_csv(bursts_input) if bursts_input is not None else None
    selected_wells = list(wells) if wells else sorted(events["well"].astype(str).unique())
    time_window_s = _parse_time_window(time_window)

    for well in selected_wells:
        figure = plot_raster(
            events,
            well=well,
            time_window_s=time_window_s,
            bursts=bursts,
            firing_rate_bin_s=bin_s,
        )
        output_path = output_dir / f"{prefix}_raster_{well}.{fmt}"
        figure.savefig(output_path, format=fmt, dpi=dpi, bbox_inches="tight")
        LOGGER.info(
            "Plotted raster well=%s n_electrodes=%s n_spikes=%s time_window=%s",
            well,
            events.loc[events["well"].astype(str) == well, "electrode"].nunique(),
            len(events.loc[events["well"].astype(str) == well]),
            time_window_s,
        )
        figure.clear()


@main.command("plot-spatial")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--prefix", required=True, type=str)
@click.option("--well", "wells", multiple=True, type=str)
@click.option("--metric", default="mean_firing_rate_hz", show_default=True, type=str)
@click.option("--grid-rows", default=4, show_default=True, type=int)
@click.option("--grid-cols", default=4, show_default=True, type=int)
@click.option("--global-scale/--per-well-scale", default=False, show_default=True)
@click.option(
    "fmt",
    "--format",
    default="png",
    show_default=True,
    type=click.Choice(["png", "pdf", "svg"]),
)
def plot_spatial_command(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    wells: tuple[str, ...],
    metric: str,
    grid_rows: int,
    grid_cols: int,
    global_scale: bool,
    fmt: Literal["png", "pdf", "svg"],
) -> None:
    """Render Workflow E spatial firing heatmaps."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(input_path)
    selected_wells = list(wells) if wells else sorted(summary["well"].astype(str).unique())
    vmin = float(summary[metric].min()) if global_scale else None
    vmax = float(summary[metric].max()) if global_scale else None

    for well in selected_wells:
        figure = plot_spatial_heatmap(
            summary,
            well=well,
            metric=metric,
            grid_shape=(grid_rows, grid_cols),
            vmin=vmin,
            vmax=vmax,
        )
        figure.savefig(
            output_dir / f"{prefix}_spatial_heatmap_{well}.{fmt}",
            format=fmt,
            dpi=150,
            bbox_inches="tight",
        )
        figure.clear()


def run_cli(args: list[str] | None = None, **extra: Any) -> Any:
    """Invoke the CLI from tests or embedding code.

    Parameters
    ----------
    args
        Optional CLI argument list.
    **extra
        Additional keyword arguments forwarded to Click.

    Returns
    -------
    Any
        Click invocation result.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    return main.main(args=args, **extra)
