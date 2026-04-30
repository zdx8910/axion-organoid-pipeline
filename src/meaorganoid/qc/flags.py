"""Workflow H (Fig. 8): public QC flag computation API."""

from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd

from meaorganoid.errors import MEAQCError

QC_FLAG_COLUMNS = (
    "qc_low_active_channels",
    "qc_short_duration",
    "qc_outlier_rate",
    "qc_status",
    "qc_reasons",
)
_BOOLEAN_FLAGS = QC_FLAG_COLUMNS[:3]
_REQUIRED_COLUMNS = ("active_channel_count", "recording_duration_s", "mean_firing_rate_hz")


@dataclass(frozen=True, slots=True)
class QCThresholds:
    """Thresholds for Workflow H QC flags.

    Parameters
    ----------
    min_active_channels
        Minimum active channels required for a recording to pass.
    min_duration_s
        Minimum recording duration in seconds.
    outlier_rate_z
        Absolute z-score threshold for firing-rate outliers within group.
    outlier_group_col
        Column used to group recordings before computing firing-rate z-scores.

    Returns
    -------
    QCThresholds
        Frozen dataclass containing QC threshold values.

    Examples
    --------
    >>> QCThresholds().min_active_channels
    4
    """

    min_active_channels: int = 4
    min_duration_s: float = 60.0
    outlier_rate_z: float = 3.0
    outlier_group_col: str = "condition"


def _validate_manifest(manifest: pd.DataFrame) -> None:
    missing = sorted(set(_REQUIRED_COLUMNS).difference(manifest.columns))
    if missing:
        raise MEAQCError(f"recording manifest: missing required QC column(s) {missing}")


def _compute_outlier_rate(manifest: pd.DataFrame, thresholds: QCThresholds) -> pd.Series:
    groups = (
        manifest[thresholds.outlier_group_col]
        if thresholds.outlier_group_col in manifest.columns
        else pd.Series("__all__", index=manifest.index)
    )
    rates = manifest["mean_firing_rate_hz"].astype(float)
    outlier = pd.Series(False, index=manifest.index, dtype=bool)

    for _, index in groups.groupby(groups, dropna=False).groups.items():
        group_rates = rates.loc[index]
        std = float(group_rates.std(ddof=0))
        if std == 0 or np.isnan(std):
            continue
        z_scores = (group_rates - float(group_rates.mean())).abs() / std
        outlier.loc[index] = z_scores > thresholds.outlier_rate_z

    return outlier


def _format_reasons(frame: pd.DataFrame) -> list[str]:
    reasons: list[str] = []
    for _, row in frame.iterrows():
        failed = [flag for flag in _BOOLEAN_FLAGS if bool(row[flag])]
        reasons.append(",".join(failed))
    return reasons


def compute_qc_flags(
    manifest: pd.DataFrame, *, thresholds: QCThresholds | None = None
) -> pd.DataFrame:
    """Compute public Workflow H QC flags for a recording manifest.

    Parameters
    ----------
    manifest
        Recording manifest with active-channel count, recording duration, and mean firing-rate
        columns.
    thresholds
        Optional QC threshold overrides. Defaults match the Workflow H public API.

    Returns
    -------
    pandas.DataFrame
        Copy of ``manifest`` with ``qc_low_active_channels``, ``qc_short_duration``,
        ``qc_outlier_rate``, ``qc_status``, and ``qc_reasons`` added or overwritten.

    Examples
    --------
    >>> manifest = pd.DataFrame(
    ...     {
    ...         "active_channel_count": [4],
    ...         "recording_duration_s": [60.0],
    ...         "mean_firing_rate_hz": [1.0],
    ...     }
    ... )
    >>> compute_qc_flags(manifest).loc[0, "qc_status"]
    'pass'
    """
    active_thresholds = thresholds or QCThresholds()
    _validate_manifest(manifest)

    frame = manifest.copy()
    frame["qc_low_active_channels"] = (
        frame["active_channel_count"].astype(int) < active_thresholds.min_active_channels
    )
    frame["qc_short_duration"] = (
        frame["recording_duration_s"].astype(float) < active_thresholds.min_duration_s
    )
    frame["qc_outlier_rate"] = _compute_outlier_rate(frame, active_thresholds)
    frame["qc_reasons"] = _format_reasons(frame)
    frame["qc_status"] = np.where(frame["qc_reasons"] == "", "pass", "fail")

    non_qc_columns = [column for column in frame.columns if column not in QC_FLAG_COLUMNS]
    return cast(pd.DataFrame, frame.loc[:, [*non_qc_columns, *QC_FLAG_COLUMNS]].copy())
