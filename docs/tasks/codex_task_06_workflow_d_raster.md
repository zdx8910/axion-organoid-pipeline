# Codex Task 06 — Workflow D: NMT-style raster plot

## Workflow context

Touches **workflow D only** (raster plots). Currently a stub from Task 01. NMT renders rasters as one row per electrode, time on the x-axis, vertical ticks at spike times, optionally with burst overlays and a per-well summary firing-rate trace. This task implements that with matplotlib.

## Pre-task

1. Read `AGENTS.md`. Plot tests verify file written and non-empty — **no pixel comparison**.
2. Read `src/meaorganoid/plot/raster.py` (stub). Look at any NMT screenshots in `legacy/references/` for the visual target.
3. Run `pytest -q`.

## What to do

1. Public function `meaorganoid.plot.raster.plot_raster`:

   ```python
   def plot_raster(
       events: pd.DataFrame,
       *,
       well: str,
       time_window_s: tuple[float, float] | None = None,
       bursts: pd.DataFrame | None = None,
       firing_rate_bin_s: float = 1.0,
       title: str | None = None,
       figsize: tuple[float, float] = (10.0, 6.0),
       ax: Axes | None = None,
   ) -> Figure:
       ...
   ```

   * `events` is the canonical Workflow A output (columns `time_s, electrode, well`).
   * Filters to one `well`. Raises `MEAValueError` if the well is missing.
   * Sorts electrodes alphanumerically (Axion labels `A1_11, A1_12, …`) — natural sort, not lexicographic — so `A1_2` comes before `A1_10`.
   * Top axes: per-electrode raster (vertical ticks, one row per electrode, y-tick labels are electrode names).
   * Bottom axes (shared x): population firing-rate trace binned at `firing_rate_bin_s`.
   * If `bursts` is provided, filter to this well, draw a translucent horizontal bar on each electrode's raster row spanning the burst's `start_s` to `end_s`.
   * `time_window_s` clips both x axes.
   * Returns the `Figure`. If `ax` is provided it must be the top axes; the function still creates the bottom axes via `subplot_mosaic` or equivalent. (In practice: prefer `subplot_mosaic` over manual `add_axes`.)

2. CLI subcommand `meaorganoid plot-raster`:
   * `--input <events.csv>` — events file from `meaorganoid process`.
   * `--bursts-input <bursts.csv>` — optional, output of `meaorganoid bursts`.
   * `--output-dir <dir>` — required.
   * `--prefix <str>` — required.
   * `--well <str>` — repeatable; if omitted, plot one figure per well present in events.
   * `--time-window <start>,<end>` — optional pair of floats in seconds.
   * `--bin-s <float>` — default `1.0`.
   * `--format [png|pdf|svg]` — default `png`.
   * `--dpi <int>` — default `150`.
   * Output filenames: `<prefix>_raster_<well>.<fmt>` — public API.

3. Logging: one INFO line per well plotted with `n_electrodes`, `n_spikes`, `time_window`. No `print()`.

4. Tutorial page `docs/tutorials/workflow-d-raster.md` showing one raster from `data/sample/`.

## Tests to add

`tests/unit/test_plot_raster.py`:

* Synthetic `events` with two wells, four electrodes, hand-placed spike times.
* Assert `plot_raster(events, well="A1")` returns a `Figure` with at least two axes.
* Assert `plot_raster(events, well="missing")` raises `MEAValueError`.
* Assert natural sort: build electrodes `["A1_1", "A1_10", "A1_2"]`, render, then read `ax.get_yticklabels()` and assert order is `A1_1, A1_2, A1_10`.
* When `bursts` is provided, assert at least one `Patch` is added to the top axes (find via `ax.patches`).

`tests/integration/test_workflow_d_cli.py` (`@pytest.mark.integration`):

* Run `meaorganoid plot-raster` against the events fixture.
* Assert exit code 0 and one `<prefix>_raster_<well>.png` file per well, all non-zero bytes.
* **Do not pixel-compare.**

## Success criteria

* Tests pass.
* `ruff`, `mypy --strict`, `pytest -q` clean.
* No new dependencies. No NetworkX, no Plotly.
* Tutorial page works against `data/sample/`.
* Output filenames `<prefix>_raster_<well>.<fmt>` declared **public API**.

## What NOT to do

* Do **not** use `seaborn` for the raster itself (matplotlib only — seaborn ticks look wrong on dense rasters). Seaborn is fine for any color palette helpers.
* Do **not** use `eventplot` if it produces unsorted lines; ensure the natural-sort contract.
* Do **not** read more files than needed. The function takes DataFrames; CSV reading is the CLI's job.
* Do **not** mutate the input `events` DataFrame.

## Deliverable

PR titled `feat(workflow-d): nmt-style raster plot + cli` with:

* CLI `--help` output.
* The output filename pattern marked **public API**.
* The tutorial page rendered from `data/sample/`.
* The tail of `pytest -q`.
* One sample PNG attached for visual review.
