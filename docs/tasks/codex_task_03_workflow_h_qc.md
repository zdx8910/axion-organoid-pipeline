# Codex Task 03 — Workflow H: QC flags + dashboard rendering

## Workflow context

This task touches **workflow H only** (QC report). The QC flag computations (`qc_low_active_channels`, `qc_short_duration`, `qc_outlier_rate`, `qc_status`, `qc_reasons`) were lifted in Task 01. They are working but un-tested and not yet renderable as a dashboard. This task pins the thresholds, gives each flag a docstring entry in `docs/methodology.md`, and adds a matplotlib-based dashboard renderer.

## Pre-task

1. Read `AGENTS.md` in full. Note the stability rules around QC flag names — those names are public API.
2. Read `src/meaorganoid/qc/` and the legacy aggregator (`legacy/scripts/aggregate_axion_summaries.py`) where the flags currently live.
3. Run `pytest -q`.

## What to do

1. In `src/meaorganoid/qc/flags.py`, expose a single public function `compute_qc_flags(manifest: pd.DataFrame, *, thresholds: QCThresholds | None = None) -> pd.DataFrame`. It returns the manifest with the five QC columns added or overwritten, in this column order: `qc_low_active_channels`, `qc_short_duration`, `qc_outlier_rate`, `qc_status`, `qc_reasons`.

2. Define `QCThresholds` as a frozen dataclass with these fields and defaults (matching what the legacy code already uses — do not change defaults silently):
   * `min_active_channels: int = 4`
   * `min_duration_s: float = 60.0`
   * `outlier_rate_z: float = 3.0`  (threshold on per-recording firing-rate z-score within group)
   * `outlier_group_col: str = "condition"`

3. `qc_status` is `"pass"` if no boolean flag is True, else `"fail"`. `qc_reasons` is a comma-joined string of the failing flag names, or `""` when status is pass.

4. Create `src/meaorganoid/qc/dashboard.py` with a public `render_dashboard(manifest: pd.DataFrame, output_path: Path, *, fmt: Literal["png", "pdf"] = "png") -> Path`. The dashboard is a single matplotlib figure with these subplots, in this order:
   * Top-left: bar chart of pass/fail counts.
   * Top-right: stacked bar of fail reasons (one bar per failing reason, height = count).
   * Bottom-left: histogram of recording durations with the `min_duration_s` threshold drawn as a vertical line.
   * Bottom-right: histogram of active-channel counts per recording with the `min_active_channels` threshold drawn as a vertical line.
   * Title: `"QC dashboard — N recordings"` where N is `len(manifest)`.
   * Save with `bbox_inches="tight"` and `dpi=150`.

5. Add a CLI subcommand `meaorganoid qc-report` that:
   * Takes `--input <path-to-recording-manifest.csv>` and `--output-dir <dir>` (both required).
   * Optional `--format` (`png` default, or `pdf`).
   * Writes the dashboard to `<output-dir>/<prefix>_qc_dashboard.<fmt>` where `<prefix>` is the manifest filename stem with `_recording_manifest` removed if present.
   * Also writes `<prefix>_qc_summary.csv` containing one row per failing reason with counts and percentages.
   * Logs INFO-level summary lines to stderr (pass count, fail count, top failure reason). No `print()`.

6. Update `docs/methodology.md` (create if absent). Add a section "QC flags" with one row per flag — name, definition, formula in plain English, default threshold, and the flag's column data type. Use a markdown table.

## Tests to add

Create `tests/unit/test_qc_flags.py` and `tests/integration/test_workflow_h_dashboard.py`.

`tests/unit/test_qc_flags.py` must:

* Build a small `pd.DataFrame` manifest in-memory covering: one recording that passes everything, one that fails low active channels, one that fails short duration, one that fails outlier rate, and one that fails two reasons simultaneously.
* Assert each flag column type and value.
* Assert `qc_status` and `qc_reasons` follow the rules above.
* Assert the function is pure (input not mutated) by snapshotting `manifest.equals` before and after.
* Test that custom `QCThresholds` are honored.

`tests/integration/test_workflow_h_dashboard.py` (mark `@pytest.mark.integration`) must:

* Run `meaorganoid qc-report` via `CliRunner` against a fixture manifest in `tests/fixtures/recording_manifest_small.csv` (create this fixture, ~10 rows, mix of pass/fail).
* Assert exit code 0.
* Assert both output files exist and the PNG is non-zero bytes.
* Snapshot the columns of `<prefix>_qc_summary.csv`.
* **Do not pixel-compare** the PNG (per AGENTS.md).

## Success criteria

* `ruff check`, `ruff format --check`, `mypy --strict src/`, `pytest -q` all pass.
* New CLI subcommand documented in `docs/cli.md` (paste the `--help` output).
* No new top-level dependencies.
* `qc_low_active_channels`, `qc_short_duration`, `qc_outlier_rate`, `qc_status`, `qc_reasons` are unchanged in name, type, and semantics.

## What NOT to do

* Do **not** rename any QC flag.
* Do **not** silently change a default threshold. If a default needs to change, raise it in the PR description and justify.
* Do **not** add Plotly, Bokeh, or Dash. Matplotlib only.
* Do **not** touch workflows other than H.

## Deliverable

PR titled `feat(workflow-h): qc flag API + matplotlib dashboard + cli subcommand` including:

* The `--help` output of `meaorganoid qc-report`.
* The tail of `pytest -q`.
* A markdown preview of the new section in `docs/methodology.md`.
* The PNG dashboard rendered against `recording_manifest_small.csv`, attached to the PR.
