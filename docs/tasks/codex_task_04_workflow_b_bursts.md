# Codex Task 04 — Workflow B: ISI-based burst detection

## Workflow context

This task touches **workflow B only**. Burst detection is a stub after Task 01. This task implements the two reference algorithms and their CLI, and freezes the output schema as public API.

## Pre-task

1. Read `AGENTS.md`. Note the dependency policy: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `click`, `pyyaml` only.
2. Read `src/meaorganoid/bursts/__init__.py` (currently a `# TODO: workflow B` stub).
3. Read `legacy/scripts/` for any prior burst-detection code; if none, this is greenfield within the scope of the AGENTS.md contract.
4. Run `pytest -q`.

## What to do

1. Create `src/meaorganoid/bursts/maxinterval.py` implementing the MaxInterval method (Legéndy & Salcman 1985 / Cocatre-Zilgien & Delcomyn 1992 form). Public function:

   ```python
   def detect_bursts_maxinterval(
       spike_times_s: np.ndarray,
       *,
       max_isi_start_s: float = 0.170,
       max_isi_end_s: float = 0.300,
       min_ibi_s: float = 0.200,
       min_burst_duration_s: float = 0.010,
       min_spikes_in_burst: int = 3,
   ) -> pd.DataFrame:
       ...
   ```

   Returns a DataFrame with columns: `burst_index, start_s, end_s, duration_s, n_spikes, mean_isi_s, intra_burst_rate_hz`. One row per burst. Empty DataFrame if no bursts. Spike-times input must be sorted, monotonic; raise `MEAValueError` otherwise.

2. Create `src/meaorganoid/bursts/logisi.py` implementing the logISI method (Pasquale et al. 2010). Public function:

   ```python
   def detect_bursts_logisi(
       spike_times_s: np.ndarray,
       *,
       isi_threshold_s: float | None = None,
       min_spikes_in_burst: int = 3,
       void_parameter: float = 0.7,
   ) -> pd.DataFrame:
       ...
   ```

   When `isi_threshold_s is None`, derive it from the log-ISI distribution by finding the first local minimum of a kernel-smoothed log-ISI histogram (use `scipy.ndimage.gaussian_filter1d` and `scipy.signal.find_peaks` on the negated KDE). The void parameter governs how deep the trough must be relative to the surrounding peaks. Same return schema as MaxInterval.

3. Create `src/meaorganoid/bursts/__init__.py` re-exporting both detectors and a top-level convenience function:

   ```python
   def detect_bursts(
       events: pd.DataFrame,
       *,
       method: Literal["maxinterval", "logisi"] = "maxinterval",
       group_by: Iterable[str] = ("well", "electrode"),
       **kwargs: Any,
   ) -> pd.DataFrame:
       ...
   ```

   `events` is the canonical Workflow A output. `detect_bursts` groups by `group_by`, applies the chosen detector to each group's `time_s` column, concatenates the results with the group keys prepended, and returns a single tidy DataFrame.

4. Add a CLI subcommand `meaorganoid bursts` with these flags (long form, public API as of this PR):
   * `--input <events.parquet|csv>` — output of `meaorganoid process` (events).
   * `--output-dir <dir>` — required.
   * `--prefix <str>` — required.
   * `--method [maxinterval|logisi]` — default `maxinterval`.
   * `--max-isi-start-s`, `--max-isi-end-s`, `--min-ibi-s`, `--min-burst-duration-s`, `--min-spikes-in-burst` — MaxInterval params.
   * `--isi-threshold-s`, `--void-parameter` — logISI params.

   Outputs (filenames are public API):
   * `<prefix>_bursts.csv` — tidy bursts with columns `well, electrode, burst_index, start_s, end_s, duration_s, n_spikes, mean_isi_s, intra_burst_rate_hz, method`.
   * `<prefix>_burst_summary.csv` — per (well, electrode) summary: `n_bursts, mean_burst_duration_s, mean_intra_burst_rate_hz, mean_ibi_s, burst_rate_hz, percent_spikes_in_bursts`.

5. Update `docs/methodology.md` with one section per method describing parameters, formulas, and defaults. Cite Legéndy & Salcman 1985, Cocatre-Zilgien & Delcomyn 1992, and Pasquale et al. 2010.

## Tests to add

Create `tests/unit/test_bursts_maxinterval.py`, `tests/unit/test_bursts_logisi.py`, and `tests/integration/test_workflow_b_cli.py`.

Unit tests must use **synthetic spike trains** with analytically known answers:

* A train of three bursts at known times with known counts → assert detected start/end/n_spikes match.
* An empty train → empty DataFrame, no exception.
* A non-monotonic train → `MEAValueError` containing the substring `"not monotonic"`.
* A train where every ISI is within `max_isi_start_s` → exactly one burst spanning the whole train.
* A train where every ISI exceeds `max_isi_start_s` → zero bursts.
* For logISI: a bimodal log-ISI distribution where the trough sits at a known value → derived threshold within 5% of expected.

Integration test (`@pytest.mark.integration`) runs `meaorganoid bursts` via `CliRunner` against a fixture events file and asserts:

* Exit code 0.
* Both output files exist and have the public-API columns.
* `n_bursts` total in `<prefix>_burst_summary.csv` equals the number of unique `burst_index` rows in `<prefix>_bursts.csv` per electrode.

## Success criteria

* All tests pass.
* `ruff check`, `ruff format --check`, `mypy --strict src/` clean.
* No new dependencies. (`scipy` already approved; do not add new modules from scipy that aren't already imported elsewhere without justification.)
* The `<prefix>_bursts.csv` and `<prefix>_burst_summary.csv` schemas are explicitly documented in the PR as **public API frozen by this PR**.

## What NOT to do

* Do **not** implement network bursts in this task. That is workflow G's domain.
* Do **not** add a third detector. Two methods are enough; later PRs can extend.
* Do **not** allow Python loops over individual spikes in hot paths — vectorize. A `for burst in bursts:` loop after detection is fine; spike-by-spike loops are not.
* Do **not** silently default `isi_threshold_s` to a magic number when `None` is passed. Derive it from the data and log the derived value at INFO.

## Deliverable

PR titled `feat(workflow-b): isi burst detection (maxinterval + logisi) + cli`. Include:

* The `--help` output of `meaorganoid bursts`.
* The schemas of the two output CSVs, called out as **public API frozen by this PR**.
* The tail of `pytest -q`.
* A short rationale for the chosen MaxInterval defaults (cite the paper page).
