"""Workflow F (Fig. 6): MEA-NAP-style group comparison helpers."""

import logging
from collections.abc import Iterable
from itertools import combinations
from typing import Literal, SupportsFloat, cast

import numpy as np
import pandas as pd
from scipy import stats

from meaorganoid.errors import MEAValueError

LOGGER = logging.getLogger(__name__)
DEFAULT_GROUP_METRICS = ("mean_firing_rate_hz", "active_channel_count", "burst_rate_hz")
GROUP_COMPARISON_COLUMNS = (
    "metric",
    "group_a",
    "group_b",
    "n_a",
    "n_b",
    "median_a",
    "median_b",
    "statistic",
    "p_raw",
    "p_adj",
    "significant",
    "effect_size_r",
)


def _validate_inputs(frame: pd.DataFrame, group_col: str, metrics: Iterable[str]) -> list[str]:
    metric_list = list(metrics)
    missing = sorted({group_col, *metric_list}.difference(frame.columns))
    if missing:
        raise MEAValueError(f"well_summary: missing required column(s) {missing}")
    return metric_list


def _filter_groups(
    frame: pd.DataFrame,
    *,
    group_col: str,
    min_n_per_group: int,
) -> pd.DataFrame:
    counts = frame[group_col].value_counts(dropna=False)
    dropped = sorted(str(group) for group, count in counts.items() if count < min_n_per_group)
    if dropped:
        LOGGER.info("Dropped groups with n < %s: %s", min_n_per_group, dropped)
    keep = counts.loc[counts >= min_n_per_group].index
    return cast(pd.DataFrame, frame.loc[frame[group_col].isin(keep)].copy())


def _p_adjust(p_values: list[float], correction: Literal["holm", "bh", "none"]) -> list[float]:
    if correction == "none":
        return p_values.copy()
    adjusted = [float("nan")] * len(p_values)
    finite = [(index, p_value) for index, p_value in enumerate(p_values) if not np.isnan(p_value)]
    ordered = sorted(finite, key=lambda item: item[1])
    total = len(ordered)
    if correction == "holm":
        running = 0.0
        for rank, (index, p_value) in enumerate(ordered):
            running = max(running, min((total - rank) * p_value, 1.0))
            adjusted[index] = running
        return adjusted
    if correction == "bh":
        running = 1.0
        for reverse_rank, (index, p_value) in enumerate(reversed(ordered), start=1):
            rank = total - reverse_rank + 1
            running = min(running, p_value * total / rank)
            adjusted[index] = min(running, 1.0)
        return adjusted
    raise MEAValueError(f"group comparison: unsupported correction {correction!r}")


def _mannwhitney_row(
    *,
    metric: str,
    group_a: str,
    group_b: str,
    values_a: np.ndarray,
    values_b: np.ndarray,
) -> dict[str, object]:
    result = stats.mannwhitneyu(values_a, values_b, alternative="two-sided", method="auto")
    n_a = values_a.size
    n_b = values_b.size
    mean_u = n_a * n_b / 2.0
    std_u = np.sqrt(n_a * n_b * (n_a + n_b + 1) / 12.0)
    z_value = (float(result.statistic) - mean_u) / std_u if std_u > 0 else 0.0
    median_a = float(np.median(values_a))
    median_b = float(np.median(values_b))
    effect_sign = np.sign(median_b - median_a) or np.sign(z_value)
    return {
        "metric": metric,
        "group_a": group_a,
        "group_b": group_b,
        "n_a": n_a,
        "n_b": n_b,
        "median_a": median_a,
        "median_b": median_b,
        "statistic": float(result.statistic),
        "p_raw": float(result.pvalue),
        "effect_size_r": float(effect_sign * abs(z_value / np.sqrt(n_a + n_b))),
    }


def _dunn_pairwise_rows(
    *,
    metric: str,
    values_by_group: dict[str, np.ndarray],
) -> list[dict[str, object]]:
    ordered_groups = [group for group, values in values_by_group.items() if values.size > 0]
    values = [values_by_group[group] for group in ordered_groups]
    all_values = np.concatenate(values)
    ranks = stats.rankdata(all_values)
    n_total = all_values.size
    _, tie_counts = np.unique(all_values, return_counts=True)
    tie_sum = float(np.sum(tie_counts**3 - tie_counts))
    tie_correction = 1.0 - tie_sum / (n_total**3 - n_total) if n_total > 1 else 1.0

    rank_start = 0
    mean_ranks: dict[str, float] = {}
    group_sizes: dict[str, int] = {}
    for group, group_values in zip(ordered_groups, values, strict=True):
        rank_end = rank_start + group_values.size
        mean_ranks[group] = float(np.mean(ranks[rank_start:rank_end]))
        group_sizes[group] = group_values.size
        rank_start = rank_end

    rows: list[dict[str, object]] = []
    for group_a, group_b in combinations(ordered_groups, 2):
        values_a = values_by_group[group_a]
        values_b = values_by_group[group_b]
        n_a = group_sizes[group_a]
        n_b = group_sizes[group_b]
        se = np.sqrt((n_total * (n_total + 1) / 12.0) * tie_correction * (1.0 / n_a + 1.0 / n_b))
        z_value = (mean_ranks[group_a] - mean_ranks[group_b]) / se if se > 0 else 0.0
        median_a = float(np.median(values_a))
        median_b = float(np.median(values_b))
        effect_sign = np.sign(median_b - median_a) or np.sign(z_value)
        rows.append(
            {
                "metric": metric,
                "group_a": group_a,
                "group_b": group_b,
                "n_a": n_a,
                "n_b": n_b,
                "median_a": median_a,
                "median_b": median_b,
                "statistic": float(z_value),
                "p_raw": float(2.0 * stats.norm.sf(abs(z_value))),
                "effect_size_r": float(effect_sign * abs(z_value / np.sqrt(n_total))),
            }
        )
    return rows


def compare_groups(
    well_summary: pd.DataFrame,
    *,
    group_col: str,
    metrics: Iterable[str] = DEFAULT_GROUP_METRICS,
    method: Literal["mannwhitneyu", "kruskal"] = "mannwhitneyu",
    correction: Literal["holm", "bh", "none"] = "holm",
    min_n_per_group: int = 3,
) -> pd.DataFrame:
    """Compare metrics across experimental groups.

    Parameters
    ----------
    well_summary
        Well- or recording-level summary table.
    group_col
        Column containing group labels.
    metrics
        Numeric metrics to compare.
    method
        Statistical method. Two groups use Mann-Whitney U; three or more groups use Kruskal-Wallis
        followed by Dunn-style pairwise rank comparisons implemented with Mann-Whitney rank tests.
    correction
        Multiple-testing correction across all output rows: ``"holm"``, ``"bh"``, or ``"none"``.
    min_n_per_group
        Minimum rows required for a group to be retained.

    Returns
    -------
    pandas.DataFrame
        One row per metric and group comparison with adjusted p-values and effect size.

    Examples
    --------
    >>> frame = pd.DataFrame(
    ...     {"group": ["a"] * 3 + ["b"] * 3, "mean_firing_rate_hz": [1, 1, 1, 2, 2, 2]}
    ... )
    >>> int(compare_groups(frame, group_col="group", metrics=["mean_firing_rate_hz"]).loc[0, "n_a"])
    3
    """
    metric_list = _validate_inputs(well_summary, group_col, metrics)
    filtered = _filter_groups(well_summary, group_col=group_col, min_n_per_group=min_n_per_group)
    groups = [str(group) for group in sorted(filtered[group_col].dropna().unique())]
    if len(groups) < 2:
        return pd.DataFrame(columns=GROUP_COMPARISON_COLUMNS)

    rows: list[dict[str, object]] = []
    for metric in metric_list:
        values_by_group = {
            group: filtered.loc[filtered[group_col].astype(str) == group, metric]
            .dropna()
            .to_numpy(dtype=float)
            for group in groups
        }
        if len(groups) >= 3:
            usable = [values for values in values_by_group.values() if values.size > 0]
            if len(usable) >= 2:
                stats.kruskal(*usable)
                rows.extend(_dunn_pairwise_rows(metric=metric, values_by_group=values_by_group))
            continue
        for group_a, group_b in combinations(groups, 2):
            values_a = values_by_group[group_a]
            values_b = values_by_group[group_b]
            if values_a.size == 0 or values_b.size == 0:
                continue
            rows.append(
                _mannwhitney_row(
                    metric=metric,
                    group_a=group_a,
                    group_b=group_b,
                    values_a=values_a,
                    values_b=values_b,
                )
            )

    p_values = [float(cast(SupportsFloat, row["p_raw"])) for row in rows]
    adjusted = _p_adjust(p_values, correction)
    for row, p_adj in zip(rows, adjusted, strict=True):
        row["p_adj"] = p_adj
        row["significant"] = bool(p_adj < 0.05) if not np.isnan(p_adj) else False
    return pd.DataFrame(rows, columns=GROUP_COMPARISON_COLUMNS)
