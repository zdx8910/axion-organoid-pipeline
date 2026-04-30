"""Workflow H (Fig. 8): QC flags and dashboard rendering."""

import pandas as pd

from meaorganoid.qc.dashboard import render_dashboard
from meaorganoid.qc.flags import QCThresholds, compute_qc_flags

__all__ = ["QCThresholds", "add_qc_flags", "compute_qc_flags", "render_dashboard"]


def add_qc_flags(
    well_summary: pd.DataFrame,
    min_active_channels: int = 4,
    min_duration_s: float = 60.0,
    outlier_z_threshold: float = 3.0,
) -> pd.DataFrame:
    """Backward-compatible alias for :func:`compute_qc_flags`.

    Parameters
    ----------
    well_summary
        Per-well or per-recording summary table with QC input columns.
    min_active_channels
        Minimum active channels required for a passing row.
    min_duration_s
        Minimum recording duration in seconds.
    outlier_z_threshold
        Absolute z-score threshold for mean firing-rate outliers.

    Returns
    -------
    pandas.DataFrame
        Copy of ``well_summary`` with public QC columns added or overwritten.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    return compute_qc_flags(
        well_summary,
        thresholds=QCThresholds(
            min_active_channels=min_active_channels,
            min_duration_s=min_duration_s,
            outlier_rate_z=outlier_z_threshold,
        ),
    )
