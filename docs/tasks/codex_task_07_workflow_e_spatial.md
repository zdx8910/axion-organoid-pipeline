# Codex Task 07 — Workflow E: spatial firing heatmap

## Workflow context

Touches **workflow E only**. Heatmap of firing rate over the well's electrode grid (Axion 24-well = 4×4 per well). Some plotting code may already exist from the Task 01 bootstrap of `plot_axion_summaries.py`. This task lifts it into a clean module, freezes the public API, and produces the missing tests and tutorial.

## Pre-task

1. Read `AGENTS.md`. Note the public-API stability of `<prefix>_spatial_heatmap_<well>.png`.
2. Read `src/meaorganoid/plot/spatial.py` (whatever the bootstrap left there) and the legacy `plot_axion_summaries.py`.
3. Read `legacy/references/axion-spike-csv.md` for the electrode-label convention. Confirm: `<well>_<row><col>` where row/col are 1-indexed digits.
4. Run `pytest -q`.

## What to do

1. Public function `meaorganoid.plot.spatial.plot_spatial_heatmap`:

   ```python
   def plot_spatial_heatmap(
       channel_summary: pd.DataFrame,
       *,
       well: str,
       metric: str = "mean_firing_rate_hz",
       grid_shape: tuple[int, int] = (4, 4),
       cmap: str = "viridis",
       vmin: float | None = None,
       vmax: float | None = None,
       annotate: bool = True,
       ax: Axes | None = None,
   ) -> Figure:
       ...
   ```

   * `channel_summary` is the per-channel output of `meaorganoid process` (columns at minimum: `well, electrode, mean_firing_rate_hz, active`).
   * Parses `electrode` strings of the form `<well>_<row><col>` to recover (row, col) coordinates 1-indexed.
   * Builds a `grid_shape`-shaped numeric matrix; cells without an electrode in that position are NaN and rendered transparent.
   * If `annotate=True`, writes the metric value (3 sig figs) in the cell.
   * Inactive electrodes are drawn with a hatched overlay (`////`) instead of a NaN cell, so the grid stays visually complete.
   * Title: `f"{well} — {metric}"`.
   * Colorbar label is the metric name.
   * Raises `MEAValueError` if `metric` is missing from `channel_summary` or `well` has no electrodes.

2. CLI subcommand `meaorganoid plot-spatial`:
   * `--input <channel_summary.csv>` — required.
   * `--output-dir <dir>` — required.
   * `--prefix <str>` — required.
   * `--well <str>` — repeatable; default = all wells.
   * `--metric <str>` — default `mean_firing_rate_hz`.
   * `--grid-rows <int>` and `--grid-cols <int>` — default 4 and 4.
   * `--global-scale / --per-well-scale` — when `--global-scale`, share `vmin/vmax` across all wells. Default `--per-well-scale`.
   * `--format [png|pdf|svg]` — default `png`.
   * Output filename: `<prefix>_spatial_heatmap_<well>.<fmt>` — public API.

3. Tutorial `docs/tutorials/workflow-e-spatial.md` rendering one heatmap per well from `data/sample/`.

## Tests to add

`tests/unit/test_plot_spatial.py`:

* Build an in-memory `channel_summary` for one well with known firing rates per electrode.
* Assert returned `Figure` has the expected number of cells (`grid_shape[0] * grid_shape[1]`).
* Assert that for an electrode flagged `active=False`, the corresponding cell has a hatched patch (find via `ax.patches`, look for non-empty `get_hatch()`).
* Assert `MEAValueError` when `metric` is missing.
* Assert `vmin/vmax` are honored when explicitly passed (read from the colorbar's mappable).

`tests/integration/test_workflow_e_cli.py` (`@pytest.mark.integration`):

* Run `meaorganoid plot-spatial` against fixture `channel_summary.csv`.
* Assert one PNG per well, all non-empty.
* Test `--global-scale` produces equal `vmin/vmax` across runs (read PNG metadata or, easier, check that the function-level call with `--global-scale` yields the same colorbar limits across wells — assert this in a unit test instead).

## Success criteria

* Tests pass.
* `ruff`, `mypy --strict`, `pytest -q` clean.
* No new dependencies.
* Output filename pattern frozen as **public API**.

## What NOT to do

* Do **not** assume Axion plates are always 24-well 4×4. Honor `grid_shape` and `--grid-rows/--grid-cols` flags.
* Do **not** silently drop electrodes that don't fit the parser. Raise `MEASchemaError` listing the offending electrode strings.
* Do **not** add any new dependency for hatching or color maps.

## Deliverable

PR titled `feat(workflow-e): spatial firing heatmap + cli` with:

* CLI `--help`.
* Output filename pattern marked **public API**.
* The tutorial page.
* Tail of `pytest -q`.
* One sample heatmap PNG attached.
