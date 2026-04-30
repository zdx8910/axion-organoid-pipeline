"""Click command-line interface for meaorganoid."""

import json
import logging
from pathlib import Path
from typing import Any, Literal, cast

import click
import pandas as pd

from meaorganoid.compare.group import compare_groups
from meaorganoid.connectivity import compute_lag_window_adjacency
from meaorganoid.io import read_axion_spike_csv
from meaorganoid.metrics import compute_channel_summary, compute_well_summary
from meaorganoid.plot.condition import plot_group_comparison
from meaorganoid.plot.spatial import plot_spatial_heatmap
from meaorganoid.qc import add_qc_flags, compute_qc_flags, render_dashboard

LOGGER = logging.getLogger(__name__)


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
    plot_spatial_heatmap(pd.read_csv(input_path), output_dir / f"{prefix}_spatial_heatmap.png")


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
@click.option("--value-column", required=True, type=str)
@click.option("--group-column", default="group", show_default=True, type=str)
def compare_group(input_path: Path, output_dir: Path, value_column: str, group_column: str) -> None:
    """Compare a numeric metric across groups."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stats_table = compare_groups(
        pd.read_csv(input_path),
        value_column=value_column,
        group_column=group_column,
    )
    stats_table.to_csv(output_dir / "group_comparison_stats.csv", index=False)


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
    plot_group_comparison(
        pd.read_csv(input_path),
        value_column=value_column,
        group_column=group_column,
        output=output_dir / f"{prefix}_group_comparison.png",
    )


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
