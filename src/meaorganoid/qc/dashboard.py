"""Workflow H (Fig. 8): matplotlib QC dashboard rendering."""

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import pandas as pd

from meaorganoid.qc.flags import QCThresholds, compute_qc_flags


def _reason_counts(manifest: pd.DataFrame) -> pd.Series:
    failing = manifest.loc[manifest["qc_reasons"] != "", "qc_reasons"]
    if failing.empty:
        return pd.Series(dtype=int)
    reasons = failing.str.split(",").explode()
    return reasons.value_counts().sort_index()


def render_dashboard(
    manifest: pd.DataFrame, output_path: Path, *, fmt: Literal["png", "pdf"] = "png"
) -> Path:
    """Render a Workflow H QC dashboard to disk.

    Parameters
    ----------
    manifest
        Recording manifest with QC input columns. QC flags are computed if missing.
    output_path
        Path where the rendered dashboard should be written.
    fmt
        Output format, either ``"png"`` or ``"pdf"``.

    Returns
    -------
    pathlib.Path
        The written dashboard path.

    Examples
    --------
    >>> from pathlib import Path
    >>> manifest = pd.DataFrame(
    ...     {
    ...         "active_channel_count": [8],
    ...         "recording_duration_s": [120.0],
    ...         "mean_firing_rate_hz": [1.2],
    ...     }
    ... )
    >>> path = render_dashboard(manifest, Path("/tmp/meaorganoid_qc_example.png"))
    >>> path.name
    'meaorganoid_qc_example.png'
    """
    thresholds = QCThresholds()
    frame = manifest.copy()
    if "qc_status" not in frame.columns or "qc_reasons" not in frame.columns:
        frame = compute_qc_flags(frame, thresholds=thresholds)

    figure, axes = plt.subplots(2, 2, figsize=(10, 7))
    figure.suptitle(f"QC dashboard — {len(frame)} recordings")

    status_counts = frame["qc_status"].value_counts().reindex(["pass", "fail"], fill_value=0)
    status_counts.plot.bar(ax=axes[0, 0], color=["#2f7d4f", "#b23b3b"], rot=0)
    axes[0, 0].set_title("Pass/fail counts")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Recordings")

    reason_counts = _reason_counts(frame)
    if reason_counts.empty:
        axes[0, 1].bar(["none"], [0], color="#777777")
    else:
        reason_counts.plot.bar(ax=axes[0, 1], color="#6f5f90", rot=30)
    axes[0, 1].set_title("Fail reasons")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("Count")

    frame["recording_duration_s"].astype(float).plot.hist(ax=axes[1, 0], bins=8, color="#4f81bd")
    axes[1, 0].axvline(thresholds.min_duration_s, color="#b23b3b", linestyle="--")
    axes[1, 0].set_title("Recording durations")
    axes[1, 0].set_xlabel("Duration (s)")

    frame["active_channel_count"].astype(float).plot.hist(ax=axes[1, 1], bins=8, color="#8a9a5b")
    axes[1, 1].axvline(thresholds.min_active_channels, color="#b23b3b", linestyle="--")
    axes[1, 1].set_title("Active-channel counts")
    axes[1, 1].set_xlabel("Active channels")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, format=fmt, bbox_inches="tight", dpi=150)
    plt.close(figure)
    return output_path
