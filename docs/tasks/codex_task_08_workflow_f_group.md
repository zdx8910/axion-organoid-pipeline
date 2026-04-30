# Codex Task 08 — Workflow F: MEA-NAP-style group comparison

## Workflow context

Touches **workflow F only**. Group comparison across many recordings (e.g., DIV30 vs DIV60, control vs treatment) using the manifest produced by Workflow A and the well/channel summaries. MEA-NAP renders these as half-violin + dot plots with statistical annotations. This task implements an equivalent in matplotlib + seaborn within the AGENTS.md dependency constraints.

## Pre-task

1. Read `AGENTS.md`. NetworkX, Plotly, Bokeh, Dash, Streamlit are forbidden. Statsmodels is forbidden — use SciPy.
2. Read `src/meaorganoid/compare/group.py` (carried from `legacy/scripts/analyze_post_stim_group.py`).
3. Read `src/meaorganoid/plot/condition.py` (carried from `legacy/scripts/plot_post_stim_group_comparison.py`).
4. Run `pytest -q`.

## What to do

1. Public function in `src/meaorganoid/compare/group.py`:

   ```python
   def compare_groups(
       well_summary: pd.DataFrame,
       *,
       group_col: str,
       metrics: Iterable[str] = (
           "mean_firing_rate_hz",
           "active_channel_count",
           "burst_rate_hz",
       ),
       method: Literal["mannwhitneyu", "kruskal"] = "mannwhitneyu",
       correction: Literal["holm", "bh", "none"] = "holm",
       min_n_per_group: int = 3,
   ) -> pd.DataFrame:
       ...
   ```

   * For two groups, default to Mann-Whitney U (two-sided). For three or more, switch automatically to Kruskal-Wallis followed by Dunn's pairwise (implement Dunn's by hand on top of Mann-Whitney pairwise; do not import a new package).
   * Drops groups with fewer than `min_n_per_group` recordings; logs the dropped groups at INFO.
   * Returns one row per (metric, comparison) with columns: `metric, group_a, group_b, n_a, n_b, median_a, median_b, statistic, p_raw, p_adj, significant, effect_size_r`.
   * Effect size is `r = Z / sqrt(N)` for Mann-Whitney; for Dunn's pairwise within Kruskal, same formula on the rank z-statistic.
   * Correction is applied across all (metric, comparison) rows produced by a single call. `none` skips correction; `p_adj == p_raw` in that case.

2. Public plotting function in `src/meaorganoid/plot/condition.py`:

   ```python
   def plot_group_comparison(
       well_summary: pd.DataFrame,
       *,
       group_col: str,
       metric: str,
       order: Sequence[str] | None = None,
       palette: str = "deep",
       stats: pd.DataFrame | None = None,
       figsize: tuple[float, float] = (6.0, 5.0),
       ax: Axes | None = None,
   ) -> Figure:
       ...
   ```

   * Half-violin on the left half of each group, individual data points (jittered) on the right half. Implement the half-violin by drawing a `seaborn.violinplot` and clipping the right half via `set_clip_path` on the violins, OR by drawing `kdeplot` per group along the y-axis. Pick one approach and document it in the docstring.
   * Median line.
   * If `stats` is provided (output of `compare_groups`), draw significance annotations (`*`, `**`, `***` based on `p_adj < 0.05, 0.01, 0.001`) connecting each significant group pair.
   * Title: the metric name. Y-axis: metric. X-axis: group labels.
   * Returns the `Figure`.

3. CLI subcommand `meaorganoid compare-group`:
   * `--input <well_summary.csv>` — required.
   * `--output-dir <dir>` — required.
   * `--prefix <str>` — required.
   * `--group-col <str>` — required.
   * `--metrics <comma-separated>` — defaults match the function default.
   * `--method [mannwhitneyu|kruskal]`, `--correction [holm|bh|none]`.
   * `--min-n-per-group <int>` — default 3.
   * Output:
     - `<prefix>_group_comparison.csv` — public API.
     - `<prefix>_group_comparison_<metric>.png` per metric — public API.

4. Tutorial `docs/tutorials/workflow-f-group.md`.

## Tests to add

`tests/unit/test_compare_group.py`:

* Build a synthetic `well_summary` with two groups (10 wells each) of known distributions.
* Assert `compare_groups` returns one row per metric with correct group labels and `n_a/n_b`.
* With identical distributions: `p_raw > 0.5`, `significant == False`.
* With shifted distributions: `significant == True`, `effect_size_r` non-trivial and same sign as the shift.
* With three groups, `method="mannwhitneyu"` should fall back to Dunn's after Kruskal — assert `len(result) == 3` (three pairwise comparisons).
* With `min_n_per_group=20`, both groups dropped, returns empty DataFrame and logs INFO.
* Holm vs BH vs none correction yields different `p_adj`.

`tests/unit/test_plot_group.py`:

* Synthetic data → returned `Figure` has axes with the expected number of x-ticks.
* When `stats` contains significant rows, assert at least one annotation line exists (`ax.lines` with the bracket pattern).

`tests/integration/test_workflow_f_cli.py`:

* Run `meaorganoid compare-group` against `tests/fixtures/well_summary_groups.csv`.
* Assert exit 0; CSV exists with correct schema; one PNG per metric exists and is non-zero.

## Success criteria

* Tests pass.
* `ruff`, `mypy --strict`, `pytest -q` clean.
* No `statsmodels`, no `pingouin`, no NetworkX. SciPy + hand-rolled correction only.
* Output filenames marked **public API**.

## What NOT to do

* Do **not** import a new stats package. Implement Holm and BH inline (≤10 lines each).
* Do **not** implement Dunn's by importing — implement on top of pairwise Mann-Whitney with a rank-sum continuity correction.
* Do **not** allow silent group drops without logging them.
* Do **not** hardcode the metric list inside the plot function; iterate from the CLI.

## Deliverable

PR titled `feat(workflow-f): mea-nap-style group comparison + cli` with:

* CLI `--help`.
* The output schemas marked **public API**.
* One sample comparison PNG attached.
* Tail of `pytest -q`.
* A short note in the description on the half-violin implementation choice (KDE vs clipped violinplot).
