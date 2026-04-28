"""Workflow F (Fig. 6): MEA-NAP-style group comparison helpers."""

import pandas as pd
from scipy import stats

from meaorganoid.errors import MEAValueError


def compare_groups(
    data: pd.DataFrame,
    value_column: str,
    group_column: str = "group",
) -> pd.DataFrame:
    """Compare a numeric value across groups with one-way ANOVA.

    Parameters
    ----------
    data
        Tidy table containing group labels and numeric values.
    value_column
        Numeric value column to compare.
    group_column
        Column containing group labels.

    Returns
    -------
    pandas.DataFrame
        Single-row ANOVA result table.

    Examples
    --------
    >>> # TODO: doctest in a later task
    """
    missing = sorted({value_column, group_column}.difference(data.columns))
    if missing:
        raise MEAValueError(f"group table: missing required column(s) {missing}")

    samples = [
        group[value_column].dropna().to_numpy(dtype=float)
        for _, group in data.groupby(group_column, dropna=False)
    ]
    usable = [sample for sample in samples if sample.size > 0]
    if len(usable) < 2:
        statistic = float("nan")
        p_value = float("nan")
    else:
        result = stats.f_oneway(*usable)
        statistic = float(result.statistic)
        p_value = float(result.pvalue)

    return pd.DataFrame(
        [
            {
                "test": "one_way_anova",
                "n_groups": len(usable),
                "statistic": statistic,
                "p_value": p_value,
            }
        ]
    )
