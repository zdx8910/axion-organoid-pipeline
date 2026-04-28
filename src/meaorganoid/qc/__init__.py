"""Workflow H (Fig. 8): QC flag computation and dashboard stub."""

from typing import cast

import numpy as np
import pandas as pd

from meaorganoid.errors import MEAQCError


def add_qc_flags(
    well_summary: pd.DataFrame,
    min_active_channels: int = 1,
    min_duration_s: float = 60.0,
    outlier_z_threshold: float = 3.0,
) -> pd.DataFrame:
    """Add recording- and well-level QC flags to a well summary table.

    Parameters
    ----------
    well_summary
        Per-well summary table containing active-channel, duration, and firing-rate columns.
    min_active_channels
        Minimum active channels required for a passing well.
    min_duration_s
        Minimum recording duration in seconds.
    outlier_z_threshold
        Absolute z-score threshold for mean firing-rate outliers.

    Returns
    -------
    pandas.DataFrame
        Copy of ``well_summary`` with QC columns appended.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    required = {"active_channel_count", "recording_duration_s", "mean_firing_rate_hz"}
    missing = sorted(required.difference(well_summary.columns))
    if missing:
        raise MEAQCError(f"well_summary: missing required QC column(s) {missing}")

    frame = well_summary.copy()
    rates = frame["mean_firing_rate_hz"].astype(float)
    rate_std = float(rates.std(ddof=0))
    if rate_std == 0 or np.isnan(rate_std):
        outlier = pd.Series(False, index=frame.index)
    else:
        outlier = ((rates - float(rates.mean())).abs() / rate_std) > outlier_z_threshold

    frame["qc_low_active_channels"] = frame["active_channel_count"] < min_active_channels
    frame["qc_short_duration"] = frame["recording_duration_s"] < min_duration_s
    frame["qc_outlier_rate"] = outlier

    reasons: list[str] = []
    for _, row in frame.iterrows():
        row_reasons = [
            name
            for name in ("qc_low_active_channels", "qc_short_duration", "qc_outlier_rate")
            if bool(row[name])
        ]
        reasons.append(";".join(row_reasons))

    frame["qc_reasons"] = reasons
    frame["qc_status"] = np.where(frame["qc_reasons"] == "", "pass", "fail")
    return cast(pd.DataFrame, frame)


def render_qc_dashboard(*_args: object, **_kwargs: object) -> None:
    """Stub for the workflow H QC dashboard renderer.

    Parameters
    ----------
    *_args
        Positional arguments reserved for a later workflow H implementation.
    **_kwargs
        Keyword arguments reserved for a later workflow H implementation.

    Returns
    -------
    None
        This stub returns ``None``.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    # TODO: workflow H
    return None
