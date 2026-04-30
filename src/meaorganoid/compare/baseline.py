"""Workflow C (Fig. 3): baseline deltas and paired condition statistics."""

import logging
from collections.abc import Iterable
from typing import cast

import numpy as np
import pandas as pd
from scipy import stats

from meaorganoid.errors import MEAValueError

LOGGER = logging.getLogger(__name__)
DELTA_REQUIRED_COLUMNS = ("condition", "well")
PAIRED_STATS_COLUMNS = (
    "metric",
    "n_pairs",
    "mean_a",
    "mean_b",
    "mean_diff",
    "ci_low",
    "ci_high",
    "wilcoxon_W",
    "wilcoxon_p",
    "p_holm",
    "significant",
)


def _validate_columns(
    frame: pd.DataFrame,
    *,
    required: Iterable[str],
    metrics: Iterable[str],
    label: str,
) -> list[str]:
    metric_list = list(metrics)
    missing = sorted(set(required).union(metric_list).difference(frame.columns))
    if missing:
        raise MEAValueError(f"{label}: missing required column(s) {missing}")
    return metric_list


def compute_well_delta(
    well_summary: pd.DataFrame,
    *,
    baseline_label: str,
    condition_col: str = "condition",
    well_col: str = "well",
    metrics: Iterable[str] = ("mean_firing_rate_hz", "active_channel_count"),
) -> pd.DataFrame:
    """Compute within-well deltas and percent changes from baseline.

    Parameters
    ----------
    well_summary
        Well-level summary table containing one row per well and condition.
    baseline_label
        Label in ``condition_col`` identifying the baseline condition.
    condition_col
        Column containing condition labels.
    well_col
        Column identifying paired wells.
    metrics
        Numeric metric columns to normalize against each well's baseline row.

    Returns
    -------
    pandas.DataFrame
        Non-baseline rows for wells with a baseline row, with ``<metric>__delta`` and
        ``<metric>__pct_change`` columns appended.

    Examples
    --------
    >>> frame = pd.DataFrame(
    ...     {
    ...         "well": ["A1", "A1"],
    ...         "condition": ["baseline", "treatment"],
    ...         "mean_firing_rate_hz": [2.0, 3.0],
    ...         "active_channel_count": [4, 6],
    ...     }
    ... )
    >>> delta = compute_well_delta(frame, baseline_label="baseline")
    >>> float(delta.loc[0, "mean_firing_rate_hz__delta"])
    1.0
    """
    metric_list = _validate_columns(
        well_summary,
        required=(condition_col, well_col),
        metrics=metrics,
        label="well_summary",
    )
    baseline_rows = well_summary.loc[well_summary[condition_col] == baseline_label]
    baseline_wells = set(baseline_rows[well_col].dropna().astype(str))
    all_wells = set(well_summary[well_col].dropna().astype(str))
    dropped_wells = sorted(all_wells.difference(baseline_wells))
    if dropped_wells:
        LOGGER.info("Dropped wells without baseline %s: %s", baseline_label, dropped_wells)

    baseline_values = baseline_rows[[well_col, *metric_list]].drop_duplicates(subset=[well_col])
    baseline_values = baseline_values.rename(
        columns={metric: f"{metric}__baseline" for metric in metric_list}
    )
    non_baseline = well_summary.loc[well_summary[condition_col] != baseline_label].copy()
    merged = non_baseline.merge(baseline_values, on=well_col, how="inner", validate="many_to_one")

    for metric in metric_list:
        baseline_col = f"{metric}__baseline"
        delta_col = f"{metric}__delta"
        pct_col = f"{metric}__pct_change"
        merged[delta_col] = merged[metric].astype(float) - merged[baseline_col].astype(float)
        baseline = merged[baseline_col].astype(float)
        merged[pct_col] = np.where(baseline == 0, np.nan, merged[delta_col] / baseline * 100.0)
        merged = merged.drop(columns=[baseline_col])
    return cast(pd.DataFrame, merged.reset_index(drop=True))


def _bootstrap_ci(diff: np.ndarray, *, n_resamples: int = 10_000) -> tuple[float, float]:
    if diff.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(0)
    sample_indices = rng.integers(0, diff.size, size=(n_resamples, diff.size))
    means = diff[sample_indices].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def _holm_correction(p_values: list[float]) -> list[float]:
    corrected = [float("nan")] * len(p_values)
    finite = [(index, p_value) for index, p_value in enumerate(p_values) if not np.isnan(p_value)]
    ordered = sorted(finite, key=lambda item: item[1])
    running = 0.0
    total = len(ordered)
    for rank, (index, p_value) in enumerate(ordered):
        adjusted = min((total - rank) * p_value, 1.0)
        running = max(running, adjusted)
        corrected[index] = running
    return corrected


def compute_paired_condition_stats(
    well_summary: pd.DataFrame,
    *,
    condition_a: str,
    condition_b: str,
    condition_col: str = "condition",
    well_col: str = "well",
    metrics: Iterable[str] = ("mean_firing_rate_hz", "active_channel_count"),
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Compute paired Wilcoxon statistics and bootstrap CIs for conditions.

    Parameters
    ----------
    well_summary
        Well-level summary table containing one row per well and condition.
    condition_a
        First condition label.
    condition_b
        Second condition label.
    condition_col
        Column containing condition labels.
    well_col
        Column identifying paired wells.
    metrics
        Numeric metric columns to compare.
    alpha
        Significance threshold after Holm correction.

    Returns
    -------
    pandas.DataFrame
        One row per metric with paired means, bootstrap CI, Wilcoxon statistic, raw p-value,
        Holm-corrected p-value, and boolean significance flag.

    Examples
    --------
    >>> frame = pd.DataFrame(
    ...     {
    ...         "well": ["A1", "A1", "A2", "A2"],
    ...         "condition": ["baseline", "treatment", "baseline", "treatment"],
    ...         "mean_firing_rate_hz": [1.0, 2.0, 2.0, 3.0],
    ...         "active_channel_count": [4, 5, 5, 6],
    ...     }
    ... )
    >>> float(
    ...     compute_paired_condition_stats(
    ...         frame, condition_a="baseline", condition_b="treatment"
    ...     ).loc[0, "mean_diff"]
    ... )
    1.0
    """
    metric_list = _validate_columns(
        well_summary,
        required=(condition_col, well_col),
        metrics=metrics,
        label="well_summary",
    )
    rows: list[dict[str, object]] = []
    p_values: list[float] = []

    for metric in metric_list:
        subset = well_summary.loc[
            well_summary[condition_col].isin([condition_a, condition_b]),
            [well_col, condition_col, metric],
        ]
        pivot = subset.pivot_table(index=well_col, columns=condition_col, values=metric)
        paired = pivot.reindex(columns=[condition_a, condition_b]).dropna()
        values_a = paired[condition_a].to_numpy(dtype=float)
        values_b = paired[condition_b].to_numpy(dtype=float)
        diff = values_b - values_a
        if diff.size == 0:
            wilcoxon_w = float("nan")
            wilcoxon_p = float("nan")
        elif bool(np.all(diff == 0)):
            wilcoxon_w = 0.0
            wilcoxon_p = 1.0
        else:
            result = stats.wilcoxon(values_a, values_b)
            wilcoxon_w = float(result.statistic)
            wilcoxon_p = float(result.pvalue)
        ci_low, ci_high = _bootstrap_ci(diff)
        p_values.append(wilcoxon_p)
        rows.append(
            {
                "metric": metric,
                "n_pairs": int(diff.size),
                "mean_a": float(np.mean(values_a)) if values_a.size else float("nan"),
                "mean_b": float(np.mean(values_b)) if values_b.size else float("nan"),
                "mean_diff": float(np.mean(diff)) if diff.size else float("nan"),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "wilcoxon_W": wilcoxon_w,
                "wilcoxon_p": wilcoxon_p,
            }
        )

    corrected = _holm_correction(p_values)
    for row, p_holm in zip(rows, corrected, strict=True):
        row["p_holm"] = p_holm
        row["significant"] = bool(p_holm < alpha) if not np.isnan(p_holm) else False
    return pd.DataFrame(rows, columns=PAIRED_STATS_COLUMNS)
