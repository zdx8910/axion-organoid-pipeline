"""Workflows C and F (Figs. 3, 6): baseline and paired-condition comparisons."""

from typing import cast

import pandas as pd
from scipy import stats

from meaorganoid.errors import MEAValueError


def compute_delta_from_baseline(
    data: pd.DataFrame,
    value_column: str,
    baseline_column: str = "condition",
    baseline_value: str = "baseline",
    group_columns: tuple[str, ...] = ("well",),
) -> pd.DataFrame:
    """Compute within-group deltas from a baseline condition.

    Parameters
    ----------
    data
        Tidy condition table.
    value_column
        Numeric value column to normalize against baseline.
    baseline_column
        Column containing condition labels.
    baseline_value
        Label identifying baseline rows.
    group_columns
        Columns defining paired groups, usually wells or samples.

    Returns
    -------
    pandas.DataFrame
        Copy of ``data`` with ``baseline_value`` and ``delta_from_baseline`` columns.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    required = set(group_columns) | {value_column, baseline_column}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise MEAValueError(f"condition table: missing required column(s) {missing}")

    baseline = (
        data.loc[data[baseline_column] == baseline_value, [*group_columns, value_column]]
        .rename(columns={value_column: "baseline_value"})
        .drop_duplicates(subset=list(group_columns))
    )
    merged = data.merge(baseline, on=list(group_columns), how="left", validate="many_to_one")
    merged["delta_from_baseline"] = merged[value_column] - merged["baseline_value"]
    return cast(pd.DataFrame, merged)


def compute_paired_condition_stats(
    data: pd.DataFrame,
    value_column: str,
    condition_column: str = "condition",
    group_column: str = "well",
) -> pd.DataFrame:
    """Compute paired t-tests for every pair of conditions.

    Parameters
    ----------
    data
        Tidy table containing paired measurements.
    value_column
        Numeric value column to compare.
    condition_column
        Column containing condition labels.
    group_column
        Column identifying paired observations.

    Returns
    -------
    pandas.DataFrame
        One row per condition pair with test statistic and p-value.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    required = {value_column, condition_column, group_column}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise MEAValueError(f"condition table: missing required column(s) {missing}")

    pivot = data.pivot_table(index=group_column, columns=condition_column, values=value_column)
    rows: list[dict[str, object]] = []
    conditions = list(pivot.columns)
    for left_index, left in enumerate(conditions):
        for right in conditions[left_index + 1 :]:
            paired = pivot[[left, right]].dropna()
            if paired.empty:
                statistic = float("nan")
                p_value = float("nan")
            else:
                result = stats.ttest_rel(paired[left], paired[right])
                statistic = float(result.statistic)
                p_value = float(result.pvalue)
            rows.append(
                {
                    "condition_a": str(left),
                    "condition_b": str(right),
                    "n_pairs": len(paired),
                    "statistic": statistic,
                    "p_value": p_value,
                }
            )
    return pd.DataFrame(rows)
