import pandas as pd

from meaorganoid.compare.group import compare_groups
from meaorganoid.plot.condition import plot_group_comparison


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": ["control"] * 8 + ["treated"] * 8,
            "mean_firing_rate_hz": [float(i) for i in range(8)] + [float(i + 10) for i in range(8)],
        }
    )


def test_plot_group_comparison_returns_figure_with_group_ticks() -> None:
    figure = plot_group_comparison(_frame(), group_col="group", metric="mean_firing_rate_hz")

    assert len(figure.axes) == 1
    assert [tick.get_text() for tick in figure.axes[0].get_xticklabels()] == [
        "control",
        "treated",
    ]
    figure.clear()


def test_plot_group_comparison_draws_significance_bracket() -> None:
    frame = _frame()
    stats = compare_groups(
        frame,
        group_col="group",
        metrics=["mean_firing_rate_hz"],
        correction="none",
    )
    figure = plot_group_comparison(
        frame,
        group_col="group",
        metric="mean_firing_rate_hz",
        stats=stats,
    )

    bracket_lines = [line for line in figure.axes[0].lines if len(line.get_xdata()) == 4]
    assert bracket_lines
    figure.clear()
