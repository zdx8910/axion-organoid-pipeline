# Codex Task 02 — Workflow A: harden ingestion and add fixtures

## Workflow context

This task touches **workflow A only** (Axion CSV → tidy events). Workflow A is the foundation every other workflow depends on, so it must be tested against realistic input shapes before B–H can rely on it.

The bootstrap (Task 01) moved the ingestion code into `src/meaorganoid/io/`. This task hardens that code, adds real fixtures, and writes the first integration test.

## Pre-task

1. Read `AGENTS.md` at the repo root in full.
2. Read `src/meaorganoid/io/__init__.py` and the matching legacy script in `legacy/scripts/process_axion_spikes_csv.py`.
3. Read `legacy/references/axion-spike-csv.md` for the column-alias contract.
4. Run `pytest -q` and confirm the suite is green.

## What to do

1. Add fixtures under `tests/fixtures/`. Each must be smaller than 100 KB:
   * `axion_minimal.csv` — 3 electrodes, 30 spikes total, canonical columns (`Time (s)`, `Electrode`).
   * `axion_aliases_timestamp.csv` — same content, column header `Timestamp` instead of `Time (s)`.
   * `axion_aliases_spiketime.csv` — column header `SpikeTime`.
   * `axion_aliases_underscore.csv` — column header `time_s`.
   * `axion_with_well.csv` — adds an explicit `Well` column with two distinct wells.
   * `axion_missing_time.csv` — has `Electrode` but no time-like column. Used for the negative test.
   * `axion_extra_whitespace.csv` — column headers padded with leading/trailing spaces.

2. In `src/meaorganoid/io/__init__.py`, ensure `read_axion_spike_csv`:
   * Strips whitespace from column headers before alias resolution.
   * Performs alias resolution case-insensitively.
   * Returns a `pd.DataFrame` with canonical columns `time_s` (float64), `electrode` (string), and `well` (string, may be empty).
   * If a `well` column was not in the input, infer it from the Axion electrode label format (`A1_11`, `B3_42`) by splitting on the underscore, **only** when every electrode label matches that pattern. If the pattern is mixed or missing, leave `well` as an empty string and emit a `logging.warning`. Do not raise.
   * Raises `MEASchemaError` (not `KeyError`, not `ValueError`) when no time alias can be resolved. The message must include the file path and the list of columns observed.
   * Has a NumPy-style docstring with a runnable `Examples` block that loads `tests/fixtures/axion_minimal.csv` via `Path(__file__).parents[3]` resolution. The doctest must pass under `pytest --doctest-modules src/meaorganoid/io`.

3. Add a small public helper `meaorganoid.io.canonical_columns()` returning the tuple `("time_s", "electrode", "well")`. Other workflows will import this rather than hard-coding strings.

4. Do **not** change CLI flag names, output filenames, or output column names. Those are public API per AGENTS.md.

## Tests to add

Create `tests/integration/test_workflow_a_ingestion.py` and `tests/unit/test_io_aliases.py`.

`tests/unit/test_io_aliases.py` must:

* Parametrize over every alias fixture and assert the returned DataFrame has the canonical columns and the same number of rows.
* Assert `axion_extra_whitespace.csv` parses successfully.
* Assert `axion_missing_time.csv` raises `MEASchemaError` whose message contains both the file path and the literal substring `columns seen:`.
* Assert that a recording with only `A1_11`-style labels gets `well == "A1"` for every row.
* Assert that a recording with mixed labels (`A1_11`, `weird_label`) gets `well == ""` and emits exactly one `WARNING`-level log record (use `caplog`).

`tests/integration/test_workflow_a_ingestion.py` must:

* Run `meaorganoid process` via the `click.testing.CliRunner` against `axion_with_well.csv`.
* Assert exit code is 0.
* Assert the four output files (`<prefix>_well_summary.csv`, `<prefix>_channel_summary.csv`, `<prefix>_run_metadata.json`, `<prefix>_input_metadata.json`) all exist.
* Snapshot the column schemas of the two CSVs (write a helper that lists columns sorted; assert against an inline expected list).
* Assert at least one numeric value (e.g., total spike count in `<prefix>_run_metadata.json`) within tolerance of a hand-computed truth value derived from the fixture.

Mark the integration test with `@pytest.mark.integration`.

## Success criteria

* All new tests pass under `pytest -q`.
* Doctest passes under `pytest --doctest-modules src/meaorganoid/io`.
* `ruff check`, `ruff format --check`, and `mypy --strict src/` all pass.
* No new top-level dependencies.
* Public API (CLI flags, output filenames, output column names) is byte-identical.

## What NOT to do

* Do **not** touch workflows B–H modules. They remain stubs from Task 01.
* Do **not** add `networkx`, `bctpy`, or any new top-level dependency.
* Do **not** change the four output filenames or any of their column names.
* Do **not** invent new error classes; use only `MEASchemaError`, `MEAValueError`, `MEAQCError`.
* Do **not** modify or delete files in `legacy/`.

## Deliverable

Open a PR titled `feat(workflow-a): harden ingestion + alias fixtures + integration test` containing:

* The list of added fixtures and their row counts.
* The tail of `pytest -q`.
* A note confirming public API is unchanged.
* A short paragraph explaining the well-inference fallback rule (so reviewers can sanity-check the heuristic).
