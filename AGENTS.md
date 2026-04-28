# AGENTS.md

This file is read by AI coding agents (Codex, Claude, etc.) at the start of every task in this repository. Follow it strictly. If a task conflicts with this file, stop and ask before proceeding.

---

## Project: `mea-organoid-toolkit`

A lightweight, CSV-first analysis toolkit for Axion microelectrode array (MEA) recordings of brain organoids. Pip-installable, stable CLI, fully tested, designed to be cited.

## The gap we fill

Most organoid MEA labs today glue together four things by hand:

1. **AxIS** (Axion's acquisition software) — produces proprietary recordings and exports spike CSVs.
2. **NMT exports** (Axion's Neural Metric Tool) — gives raster-style visualizations and per-recording metrics, but is GUI-bound and hard to script across many recordings.
3. **MEA-NAP** (MATLAB-based) — strong cross-recording comparison and group statistics, but requires MATLAB licenses, has a steep learning curve, and is not designed around the Axion CSV schema.
4. **Ad-hoc Python / Jupyter scripts** — reinvented in every lab, rarely shared, never validated against a reference.

The result: every organoid lab pays the same integration tax, reproducibility suffers, and Methods sections cite "custom scripts."

**This toolkit formalizes that glue layer.** It starts from Axion spike CSV exports (post-detection) and ends at publication-quality, reproducible figures and tidy tables. It does not replace AxIS, NMT, or MEA-NAP — it bridges them with a single tested Python codebase and a stable CLI.

## Scope

**In scope:**

- Axion spike CSV ingestion with robust column-alias resolution
- Per-channel and per-well firing metrics (rate, ISI stats, active-channel counts)
- ISI-based burst detection (algorithms documented in `docs/methodology.md`)
- Baseline normalization (within-well delta from pre-stim/untreated baseline)
- Paired condition statistics
- NMT-style raster plots driven from spike CSVs
- Spatial firing heatmaps over the well electrode layout
- MEA-NAP-style group comparisons across many recordings
- Functional connectivity network plotting (lag-windowed)
- Configurable QC flags and a QC dashboard

**Explicitly out of scope:**

- Parsing Axion proprietary raw recordings (`.raw`, `.spk`)
- Running spike detection on raw voltage traces
- Real-time or streaming analysis
- 2D dissociated-culture-specific optimizations
- Heavyweight ML (no PyTorch, no TensorFlow, no JAX as dependencies)

If a task requires extending scope, **stop and flag it in the PR description** rather than silently adding new dependencies.

## Audience

Wet-lab and computational researchers running Axion Maestro MEA experiments on cortical, midbrain, or other brain organoids. Assume:

- They are comfortable with the command line.
- They are not necessarily Python developers.
- They want `pip install` + one CLI command from CSV to figure.
- They will cite the paper if the tool works on their data.

---

## The eight reference workflows (A–H)

These are the canonical pipelines the toolkit supports. **Every paper figure maps to one of these.** Tests, docs, tutorials, and module names are organized around them.

| ID | Workflow                                  | Module                          | Paper figure |
|----|-------------------------------------------|---------------------------------|--------------|
| A  | **Ingestion** — Axion CSV → tidy events    | `meaorganoid.io`                | Fig. 1       |
| B  | **Burst detection** — ISI-based bursts     | `meaorganoid.bursts`            | Fig. 2       |
| C  | **Baseline normalization** — within-well delta from baseline | `meaorganoid.compare`  | Fig. 3       |
| D  | **Raster (NMT-style)** — spike rasters with electrode/well annotation | `meaorganoid.plot.raster` | Fig. 4 |
| E  | **Spatial heatmap** — firing rate over well electrode layout | `meaorganoid.plot.spatial` | Fig. 5 |
| F  | **Group comparison (MEA-NAP-style)** — across datasets with QC and stats | `meaorganoid.compare.group` | Fig. 6 |
| G  | **Functional connectivity** — pairwise lag-windowed network plot | `meaorganoid.connectivity` | Fig. 7 |
| H  | **QC report** — recording- and well-level QC dashboard | `meaorganoid.qc`        | Fig. 8       |

When implementing, refactoring, or testing anything, name it after the workflow it serves and cross-reference the figure number in docstrings and PR descriptions.

---

## Repository layout

```
src/meaorganoid/
├── io/              # A: ingestion, alias resolution, schema validation
├── metrics/         # firing rate, ISI stats, active-channel counts
├── bursts/          # B: ISI-based burst detection
├── compare/         # C, F: baseline delta, group comparison, paired stats
├── qc/              # H: QC flags and dashboard
├── plot/
│   ├── raster.py    # D
│   ├── spatial.py   # E
│   └── condition.py # F figures
├── connectivity/    # G: pairwise network plotting
├── cli/             # CLI entry points (one module per subcommand)
├── errors.py        # MEAValueError, MEASchemaError, MEAQCError
└── _typing.py       # shared type aliases
tests/
├── unit/
├── integration/     # full-pipeline runs against fixtures
└── fixtures/        # small anonymized sample CSVs (<5 MB each)
notebooks/           # one notebook per paper figure (figure1_ingestion.ipynb ...)
docs/                # mkdocs-material site
data/sample/         # demo dataset used by quickstart and CI
paper/               # manuscript, figures, references
```

**Do not create files outside this layout without justification in the PR.**

---

## Coding conventions

- **Python 3.10+.** Use `match`, `|` unions, `dataclass(slots=True)` freely.
- **Type hints required** on all public functions. Use `pandas.DataFrame` and `pathlib.Path` directly; do not invent custom wrappers.
- **NumPy-style docstrings** on all public functions and classes. Always include `Parameters`, `Returns`, and `Examples` sections.
- **Formatter:** `ruff format`. **Linter:** `ruff check --select=E,F,W,I,N,UP,B,SIM,RUF`.
- **Typechecker:** `mypy --strict` on `src/`.
- **Imports:** absolute, sorted by `ruff`. No `from x import *`.
- **Logging:** use `logging.getLogger(__name__)`. Never `print()` in library code; CLIs may print structured progress to stderr.
- **Errors:** raise `MEAValueError`, `MEASchemaError`, or `MEAQCError` from `meaorganoid.errors`. Always include the offending file path and column name in the message.
- **Pandas:** prefer method chains over reassignment. Use `.copy()` defensively when returning slices of inputs.
- **NumPy:** vectorize. No Python loops over individual spikes in hot paths.
- **Filenames:** snake_case Python files; outputs use `<prefix>_<artifact>.<ext>`.

## Public API and stability

The following are **public API**. Breaking changes require a major version bump and a CHANGELOG entry:

- All CLI subcommand names and flags (`meaorganoid process --input ...`, etc.)
- All output filename conventions (`<prefix>_well_summary.csv`, `<prefix>_channel_summary.csv`, `<prefix>_run_metadata.json`, `<prefix>_input_metadata.json`, `<prefix>_recording_manifest.csv`, `<prefix>_well_delta_from_baseline.csv`, `<prefix>_paired_condition_stats.csv`)
- Column names in output CSVs
- QC flag names: `qc_low_active_channels`, `qc_short_duration`, `qc_outlier_rate`, `qc_status`, `qc_reasons`
- The `meaorganoid.io.read_axion_spike_csv` signature

Internal helpers (anything prefixed with `_`) can change freely.

## Column alias resolution

The toolkit accepts these aliases (case-insensitive, whitespace-trimmed):

- **time:** `Time (s)`, `Time`, `Timestamp`, `Spike Time`, `SpikeTime`, `time_s`
- **electrode:** `Electrode`, `Channel`, `Electrode Name`, `Channel Label`
- **well (optional):** `Well`, `Well Label`, `Well ID`, `WellName`

If a required field is missing after alias resolution, raise `MEASchemaError` with the file path and the list of columns that were seen. **Never silently fall back to defaults.**

## Dependencies policy

Top-level runtime dependencies are exactly: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `click`, `pyyaml`.

**Do not add a new top-level dependency without a one-paragraph justification in the PR.** Specifically forbidden: PyTorch, TensorFlow, JAX, NetworkX (we use simple adjacency matrices), Plotly, Bokeh, Dash, Streamlit. If a feature truly needs one of these, propose it as an optional extra (`pip install meaorganoid[interactive]`) and gate the import behind a try/except with a clear error.

---

## Testing requirements

- Every public function needs at least one unit test.
- Every workflow A–H needs an integration test that runs the CLI end-to-end against `tests/fixtures/` and asserts on (a) output file existence, (b) output file column schema, and (c) at least one numeric value within tolerance.
- Snapshot-test the column schemas of all output CSVs.
- Plot tests verify that figure files are written and non-empty. **Do not pixel-compare** — matplotlib renders differ across platforms.
- Run `pytest -q` before declaring a task done. Paste the tail of the output in the PR description.

## Documentation requirements

- Every public function: NumPy docstring with at least one `Examples` block that runs under `pytest --doctest-modules`.
- Every workflow A–H: a tutorial page in `docs/tutorials/<workflow>.md` that runs against `data/sample/` and produces the corresponding paper figure.
- Every CLI subcommand: an entry in `docs/cli.md` generated from `--help`.
- Every QC flag: a row in `docs/methodology.md` with definition, formula, and default threshold.

---

## Domain glossary (do not fight these terms)

- **MEA** — microelectrode array.
- **Well** — a single culture chamber on a multi-well plate (typically 6, 24, 48, or 96 wells per plate).
- **Electrode / channel** — a single recording site within a well. Axion 24-well plates have 16 electrodes per well in a 4×4 grid.
- **Active channel** — an electrode whose firing rate exceeds a configurable threshold (default: 0.1 Hz over the recording duration).
- **Spike** — a detected action potential timestamp from Axion's acquisition software. **We do not re-detect spikes.**
- **Burst** — a cluster of spikes on a single electrode meeting an ISI criterion. Definitions in `meaorganoid.bursts`.
- **Network burst** — a burst spanning multiple electrodes within a well, defined by simultaneity windows.
- **DIV** — days in vitro. Organoid age. Treat as critical metadata; never drop.
- **Baseline** — the pre-stimulation or untreated reference condition for a given well, used for delta computation.
- **NMT** — Axion's Neural Metric Tool; the reference for raster-style figures.
- **MEA-NAP** — the MATLAB MEA Network Analysis Pipeline; the reference for group-level comparisons.
- **AxIS** — Axion's acquisition and export software.

## Pre-task checklist for the agent

Before changing any code:

1. Read this file in full.
2. Read `README.md` and the `__init__.py` docstring of the relevant module.
3. Run `pytest -q` and confirm the suite is green on the current branch. If it is not, stop and report.
4. For any change touching workflow A–H, re-read the corresponding tutorial notebook to confirm user-facing behavior.
5. For any new dependency, stop and ask.

## Definition of done

A task is done when **all** of the following are true:

- [ ] Code changes are confined to the relevant module(s).
- [ ] `ruff check`, `ruff format --check`, `mypy --strict src/`, and `pytest -q` all pass.
- [ ] New public functions have NumPy docstrings with runnable `Examples`.
- [ ] If a workflow (A–H) was touched, its tutorial notebook still runs end-to-end against `data/sample/`.
- [ ] If output schemas changed, snapshot tests are updated and the change is called out in the PR.
- [ ] No new top-level dependencies without explicit approval.
- [ ] PR description includes: what changed, which workflow(s) (A–H) it affects, and the tail of the test output.

---

## Anti-patterns (do not do these)

- ❌ Adding a `utils.py` grab-bag. Helpers belong in the workflow module they serve.
- ❌ Reimplementing column-alias logic locally. Use `meaorganoid.io.resolve_columns`.
- ❌ Calling `print()` from a library module.
- ❌ Returning untyped dicts from public functions. Use a `dataclass` or `TypedDict`.
- ❌ Adding a CLI flag without updating `docs/cli.md` and a doctest.
- ❌ "Drive-by refactors" outside the task's stated scope.
- ❌ Mocking pandas. Use real fixtures from `tests/fixtures/`.
- ❌ Pixel-comparing figures in tests.
- ❌ Silently changing default QC thresholds.

## Communication style for the agent

When working on a task:

- **Open with:** which workflow (A–H) the task touches and which files you plan to change.
- **If ambiguous:** list the ambiguities, pick the most defensible interpretation, and state it explicitly. Do not silently expand scope.
- **Reference paper figure numbers** in commit messages and PR descriptions when the change affects a figure.
- **Close with:** the tail of `pytest -q` and a one-line summary of what changed.
