# Codex Task 05 — Workflow C: baseline normalization + paired stats

## Workflow context

This task touches **workflow C only** (within-well delta from baseline + paired condition stats). Some of this logic was carried over by Task 01. This task hardens it, freezes the output schema, adds the missing tests, and writes the tutorial.

## Pre-task

1. Read `AGENTS.md`. Note the public-API freeze on `<prefix>_well_delta_from_baseline.csv` and `<prefix>_paired_condition_stats.csv`.
2. Read `src/meaorganoid/compare/` and the legacy implementations the bootstrap pulled from.
3. Run `pytest -q`.

## What to do

1. Public functions in `src/meaorganoid/compare/baseline.py`:

   ```python
   def compute_well_delta(
       well_summary: pd.DataFrame,
       *,
       baseline_label: str,
       condition_col: str = "condition",
       well_col: str = "well",
       metrics: Iterable[str] = ("mean_firing_rate_hz", "active_channel_count"),
   ) -> pd.DataFrame:
       ...
   ```

   For each well, locate its baseline row (where `condition_col == baseline_label`). Subtract baseline metric values from every other row of that well to produce delta columns named `<metric>__delta`. Also produce `<metric>__pct_change`. Wells without a baseline row are dropped with a single INFO log line listing the dropped wells. Raise `MEAValueError` if any metric column is missing from `well_summary`.

   ```python
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
       ...
   ```

   Pairs each well across the two conditions. Computes Wilcoxon signed-rank (paired) and a paired bootstrap 95% CI of the mean difference (10000 resamples, fixed seed `0`, `numpy.random.default_rng(0)`). Returns one row per metric with columns: `metric, n_pairs, mean_a, mean_b, mean_diff, ci_low, ci_high, wilcoxon_W, wilcoxon_p, p_holm`. Holm correction is across the metrics in the call. Mark rows with `p_holm < alpha` in a boolean `significant` column.

2. CLI subcommand `meaorganoid compare-baseline`:
   * `--input <well_summary.csv>` (output of `meaorganoid process`)
   * `--output-dir <dir>`
   * `--prefix <str>`
   * `--baseline-label <str>` (required)
   * `--condition-col <str>` default `condition`
   * `--metrics <comma-separated>` default `mean_firing_rate_hz,active_channel_count`
   * Output: `<prefix>_well_delta_from_baseline.csv` (public API, do not rename).

3. CLI subcommand `meaorganoid compare-conditions`:
   * `--condition-a <str>` and `--condition-b <str>` (required).
   * Other flags as above.
   * Output: `<prefix>_paired_condition_stats.csv` (public API, do not rename).

4. Tutorial page `docs/tutorials/workflow-c-baseline.md`. Use `data/sample/` as input. Show one delta example and one paired-stats example. Include the resulting tables inline.

## Tests to add

Create `tests/unit/test_compare_baseline.py` and `tests/integration/test_workflow_c_cli.py`.

`tests/unit/test_compare_baseline.py` must:

* Build a small in-memory `well_summary` with 4 wells × 2 conditions (`baseline`, `treatment`).
* Assert `compute_well_delta` returns rows only for `treatment`, with `mean_firing_rate_hz__delta` equal to hand-computed values.
* Test the missing-baseline case: one well lacks `baseline` → it is dropped, others survive, exactly one INFO log emitted.
* Test the missing-metric case: passing `metrics=["nonexistent"]` raises `MEAValueError` whose message names the missing metric.
* For `compute_paired_condition_stats`:
  - With identical synthetic distributions across conditions → `mean_diff` is `0.0`, `wilcoxon_p` is high, `significant` is False.
  - With a deterministic shift → `mean_diff` matches the shift exactly, `significant` is True.
  - Fixed seed → bootstrap CI is reproducible across runs.

Integration test (`@pytest.mark.integration`):

* `tests/fixtures/well_summary_paired.csv` (create it: 6 wells × 2 conditions, hand-pickable means).
* Run `meaorganoid compare-baseline` and `meaorganoid compare-conditions`; assert exit codes 0, output files exist, schemas match snapshots.

## Success criteria

* All tests pass; doctests on new public functions pass.
* `ruff`, `mypy --strict`, `pytest -q` clean.
* `<prefix>_well_delta_from_baseline.csv` and `<prefix>_paired_condition_stats.csv` filenames and schemas unchanged from Task 01 except for the explicitly added columns. If anything else changed, call it out and update the public-API table in `AGENTS.md` (this requires explicit approval — flag it instead of doing it).
* Tutorial page renders cleanly and runs against `data/sample/`.

## What NOT to do

* Do **not** add `statsmodels`. SciPy and a hand-rolled Holm correction are sufficient.
* Do **not** silently rename a column.
* Do **not** change the default `alpha`. If a study needs a different alpha, it passes the flag.
* Do **not** vectorize the bootstrap by sacrificing seed reproducibility.

## Deliverable

PR titled `feat(workflow-c): baseline delta + paired stats hardening` containing:

* The two CLI `--help` outputs.
* The two output CSV schemas, marked **public API**.
* Tail of `pytest -q`.
* The rendered tutorial page (preview link or screenshot).
