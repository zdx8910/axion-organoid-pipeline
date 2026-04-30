# Codex Task 01 — Bootstrap the package skeleton

## Workflow context

This task touches **all eight workflows (A–H)** at the structural level. It does **not** implement new features. It only moves existing code from `legacy/scripts/` into the `src/meaorganoid/` layout described in `AGENTS.md` so that subsequent tasks can target individual workflows in isolation.

## Pre-task

1. Read `AGENTS.md` at the repo root in full. The repo layout, dependency policy, error class names, public-API stability rules, and anti-patterns there are binding.
2. Read every script in `legacy/scripts/` to understand the existing CLI surface — flag names, output filenames, and column conventions. These are public API and **must not change** in this task.
3. Read `legacy/references/axion-spike-csv.md` for the column-alias contract.
4. Run `pytest -q` and confirm the suite is green (it will be near-empty; that is fine).

## What to do

Convert the scripts in `legacy/scripts/` into the package layout in `AGENTS.md`. Preserve behavior. Preserve CLI flag names. Preserve output filenames. Preserve column names in output CSVs.

Concretely:

1. Create the directory tree under `src/meaorganoid/` exactly as specified in AGENTS.md, including empty `__init__.py` files.
2. Move logic into modules by responsibility:
   - CSV reading + column-alias resolution → `src/meaorganoid/io/__init__.py` (export `read_axion_spike_csv`, `resolve_columns`).
   - Channel- and well-level firing rate, ISI summary, active-channel counts → `src/meaorganoid/metrics/`.
   - Aggregation across recordings + QC flag computation (`qc_low_active_channels`, `qc_short_duration`, `qc_outlier_rate`, `qc_status`, `qc_reasons`) → `src/meaorganoid/qc/`.
   - Baseline delta and paired condition stats → `src/meaorganoid/compare/`.
   - Group-comparison logic from `analyze_post_stim_group.py` → `src/meaorganoid/compare/group.py`.
   - Plotting (heatmaps, distribution, top electrodes, group comparison plots) → `src/meaorganoid/plot/`.
   - Connectivity network plot → `src/meaorganoid/connectivity/`.
3. Wire all CLIs through one `click`-based entry point at `src/meaorganoid/cli/__init__.py` exposing `main()`. Subcommand mapping:
   - `meaorganoid process` ← `process_axion_spikes_csv.py`
   - `meaorganoid batch` ← `batch_process_axion_spikes.py`
   - `meaorganoid aggregate` ← `aggregate_axion_summaries.py`
   - `meaorganoid plot` ← `plot_axion_summaries.py`
   - `meaorganoid pipeline` ← `run_all_mea_pipeline.py`
   - `meaorganoid compare-group` ← `analyze_post_stim_group.py`
   - `meaorganoid plot-group` ← `plot_post_stim_group_comparison.py`
   - `meaorganoid connectivity` ← `plot_connectivity_network.py`
4. Every existing CLI flag (long form) and every output filename must be preserved verbatim. These are public API per AGENTS.md.
5. Add type hints to every public function moved into the new layout. Use `pandas.DataFrame` and `pathlib.Path` directly.
6. Add NumPy-style docstrings to every public function. The `Examples` section may be a single-line placeholder (`>>> # TODO: doctest in a later task`).
7. Create `src/meaorganoid/errors.py` defining `MEAValueError`, `MEASchemaError`, `MEAQCError`. Replace existing `ValueError`/`KeyError` raises in moved code with these where they refer to schema or QC failures. Always include the offending file path and column name in the message.
8. Add `src/meaorganoid/__init__.py` exposing `__version__` from package metadata and re-exporting the most-used top-level symbols (`read_axion_spike_csv`, error classes).

## Tests to add

Create exactly **one** test file: `tests/unit/test_io_smoke.py`. It must:

1. Build a tiny in-memory CSV using each supported `time` column alias (`Time (s)`, `Time`, `Timestamp`, `Spike Time`, `SpikeTime`, `time_s`), pass it through `read_axion_spike_csv`, and assert the returned DataFrame has the canonical columns.
2. Build a CSV missing any time column and assert `read_axion_spike_csv` raises `MEASchemaError` with a message containing the file path.

Workflow-specific tests are tracked separately and are **not** part of this task.

## Success criteria

All of these must hold before opening the PR:

- `pip install -e ".[dev]"` succeeds in a clean venv.
- `meaorganoid --help` lists all eight subcommands above.
- For every old `python legacy/scripts/X.py --help`, the equivalent `meaorganoid <subcommand> --help` shows the same long-form flags.
- `ruff check` passes.
- `ruff format --check` passes.
- `mypy --strict src/` passes.
- `pytest -q` passes (only the new smoke test runs).
- No new top-level dependencies were added beyond those declared in `pyproject.toml`.
- `legacy/` is byte-identical to before.

## What NOT to do

- Do **not** implement burst detection (workflow B). Leave `src/meaorganoid/bursts/__init__.py` as a stub with a `# TODO: workflow B` comment.
- Do **not** implement the NMT-style raster plot (workflow D). Leave a stub.
- Do **not** implement the QC dashboard rendering (workflow H) — only the QC flag computation that already exists in the legacy aggregator. Leave a dashboard stub.
- Do **not** change algorithmic behavior of any moved code.
- Do **not** modify or delete files in `legacy/`.
- Do **not** add a `utils.py` grab-bag.
- Do **not** add a new top-level dependency.

## Deliverable

Open a PR titled `chore: bootstrap package skeleton from legacy scripts` containing:

- A description listing every old script → new module mapping (one line each).
- The tail of `pytest -q` output.
- A note confirming all CLI long-form flags and output filenames were preserved verbatim.
- A note confirming which workflow modules are stubs vs. implemented in this task.
