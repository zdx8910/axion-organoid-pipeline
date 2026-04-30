"""Workflows C and F (Figs. 3, 6): condition comparison helpers."""

import pandas as pd

from meaorganoid.compare.baseline import compute_paired_condition_stats, compute_well_delta
from meaorganoid.compare.group import compare_groups

__all__ = [
    "compare_groups",
    "compute_delta_from_baseline",
    "compute_paired_condition_stats",
    "compute_well_delta",
]


def compute_delta_from_baseline(
    data: pd.DataFrame,
    value_column: str,
    baseline_column: str = "condition",
    baseline_value: str = "baseline",
    group_columns: tuple[str, ...] = ("well",),
) -> pd.DataFrame:
    """Backward-compatible alias for :func:`compute_well_delta`.

    Parameters
    ----------
    data
        Tidy condition table.
    value_column
        Metric column to normalize.
    baseline_column
        Column containing condition labels.
    baseline_value
        Label identifying baseline rows.
    group_columns
        Columns defining paired groups. The first column is used as the well identifier.

    Returns
    -------
    pandas.DataFrame
        Non-baseline rows with delta and percent-change columns.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    return compute_well_delta(
        data,
        baseline_label=baseline_value,
        condition_col=baseline_column,
        well_col=group_columns[0],
        metrics=(value_column,),
    )
