# Codex Task 09 — Workflow G: functional connectivity network (lag-windowed STTC)

## Workflow context

Touches **workflow G only**. AGENTS.md says "we use simple adjacency matrices" — that is a constraint on the *plotting layer* (no NetworkX). It does not forbid a defensible coefficient. This task uses the **Spike Time Tiling Coefficient (STTC; Cutts & Eglen 2014)** computed in pure NumPy, with **circular-shift probabilistic thresholding** for edge significance. Plotting is matplotlib only, on the well's electrode grid coordinates already used by Workflow E.

## Pre-task

1. Read `AGENTS.md`. Confirm: no NetworkX, no `bctpy`, no `brainconn`. NumPy-only adjacency.
2. Read Cutts & Eglen 2014 if you don't already know STTC. The reference implementation is ~25 lines.
3. Read `src/meaorganoid/connectivity/__init__.py` (stub from Task 01) and `legacy/scripts/plot_connectivity_network.py`.
4. Read `src/meaorganoid/plot/spatial.py` from Task 07 for the electrode-coordinate parser; reuse it.
5. Run `pytest -q`.

## What to do

1. Public function `meaorganoid.connectivity.sttc.compute_sttc`:

   ```python
   def compute_sttc(
       spike_train_a: np.ndarray,
       spike_train_b: np.ndarray,
       *,
       lag_s: float,
       recording_duration_s: float,
   ) -> float:
       ...
   ```

   * Both inputs are sorted 1-D arrays of spike times in seconds.
   * Returns a float in `[-1.0, 1.0]`. Returns `np.nan` if either train is empty (do not raise).
   * Vectorize the "fraction of time within ±lag of any spike" calculation. No Python loops over individual spikes in this function.

2. Public function `meaorganoid.connectivity.adjacency.build_sttc_adjacency`:

   ```python
   def build_sttc_adjacency(
       events: pd.DataFrame,
       *,
       well: str,
       lag_s: float,
       recording_duration_s: float,
       min_spikes: int = 10,
   ) -> tuple[np.ndarray, list[str]]:
       ...
   ```

   Filters to one well, keeps only electrodes with at least `min_spikes` spikes, computes the upper triangle of the STTC matrix, mirrors it, sets the diagonal to `1.0`. Returns `(adjacency, electrode_labels)` where `electrode_labels[i]` is the electrode at row/column `i`. Empty wells return `(np.zeros((0, 0)), [])` without raising.

3. Public function `meaorganoid.connectivity.threshold.probabilistic_threshold`:

   ```python
   def probabilistic_threshold(
       events: pd.DataFrame,
       *,
       well: str,
       lag_s: float,
       recording_duration_s: float,
       n_iterations: int = 200,
       percentile: float = 95.0,
       seed: int | None = 0,
       min_spikes: int = 10,
   ) -> tuple[np.ndarray, np.ndarray]:
       ...
   ```

   For each electrode pair, generate `n_iterations` circular-shifted versions of one train, compute STTC each time, and threshold the real STTC against the per-pair `percentile`. Returns `(adjacency_thresholded, significance_mask)` where `significance_mask` is boolean. Use `numpy.random.default_rng(seed)`. Vectorize across pairs where possible — at minimum do not nest a Python loop over both pairs and iterations.

4. Public function `meaorganoid.connectivity.plot.plot_connectivity_network`:

   ```python
   def plot_connectivity_network(
       adjacency: np.ndarray,
       electrode_labels: list[str],
       *,
       channel_summary: pd.DataFrame,
       grid_shape: tuple[int, int] = (4, 4),
       edge_threshold: float = 0.0,
       node_metric: str = "mean_firing_rate_hz",
       node_cmap: str = "viridis",
       edge_alpha_scale: bool = True,
       title: str | None = None,
       ax: Axes | None = None,
   ) -> Figure:
       ...
   ```

   * Place each electrode at its (row, col) parsed from its label (reuse Workflow E's parser).
   * Draw nodes as colored circles sized by `node_metric` from `channel_summary`.
   * Draw edges as line segments between node centers. Edge width scales with `|adjacency[i, j]|`. If `edge_alpha_scale`, edge alpha also scales. Skip edges with `|adjacency[i, j]| <= edge_threshold`.
   * Add a colorbar for nodes and a legend for edge weights.

5. CLI subcommand `meaorganoid connectivity`:
   * `--input <events.csv>` — required.
   * `--channel-summary <channel_summary.csv>` — required (for node sizing).
   * `--manifest <recording_manifest.csv>` — required (for `recording_duration_s` per recording).
   * `--output-dir <dir>` — required.
   * `--prefix <str>` — required.
   * `--well <str>` — repeatable; default = all wells.
   * `--lag-s <float>` — default `0.05` (50 ms).
   * `--n-iterations <int>` — default `200`.
   * `--percentile <float>` — default `95.0`.
   * `--min-spikes <int>` — default `10`.
   * `--seed <int>` — default `0`.
   * `--edge-threshold <float>` — default `0.0` (after probabilistic thresholding).
   * `--format [png|pdf|svg]` — default `png`.
   * Outputs (public API):
     - `<prefix>_connectivity_<well>.<fmt>`
     - `<prefix>_connectivity_<well>.npz` containing keys `adjacency`, `significance_mask`, `electrode_labels`, and the parameter dict as `params` (a 0-d object array). Saving the adjacency lets downstream tooling reuse it without re-running thresholding.

6. Update `docs/methodology.md` with an STTC section: definition, formula, the lag and percentile defaults, a note that `min_spikes=10` follows MEA-NAP convention.

7. Tutorial `docs/tutorials/workflow-g-connectivity.md` from `data/sample/`.

## Tests to add

`tests/unit/test_sttc.py`:

* Identical trains: `compute_sttc(t, t, lag_s=0.01, T=10) == 1.0` (within 1e-9).
* Empty train: returns `np.nan`, does not raise.
* Disjoint trains with no overlap windows: STTC near 0.
* A small hand-computed example: 2 spikes vs 2 spikes with known coincidence count → STTC matches the formula by hand.

`tests/unit/test_adjacency.py`:

* `build_sttc_adjacency` on a hand-built `events` DataFrame: assert symmetry, diagonal all 1, off-diagonal values in `[-1, 1]` or NaN.
* `min_spikes` filter: electrodes with too few spikes are excluded from the matrix and labels.

`tests/unit/test_probabilistic_threshold.py`:

* With `seed=0`, two runs return identical adjacency matrices.
* For two trains generated independently from a Poisson process with no coupling, the significance mask off-diagonal is mostly False (assert mean significance < 0.10 over a small synthetic example).
* For two strongly coupled trains, the mask is True (assert mean significance > 0.80).
* `n_iterations=0` raises `MEAValueError`.

`tests/integration/test_workflow_g_cli.py`:

* Run `meaorganoid connectivity` against `data/sample/` (or a tiny fixture if sample is too large for CI).
* Assert exit 0, one PNG and one NPZ per well, both non-empty.
* Open the NPZ and assert the adjacency is symmetric and the diagonal is 1.

## Success criteria

* Tests pass.
* `ruff`, `mypy --strict`, `pytest -q` clean.
* No new top-level dependencies — NumPy is enough.
* Output filenames frozen as **public API**.
* Methodology doc updated; tutorial runs against `data/sample/`.

## What NOT to do

* Do **not** add NetworkX, `bctpy`, `brainconn`, or `igraph`.
* Do **not** loop over individual spike times in `compute_sttc`. Vectorize using interval arithmetic.
* Do **not** seed inside the loop — seed once via `default_rng(seed)`.
* Do **not** silently change the percentile or n_iterations defaults from the AGENTS.md / methodology values once they are documented.

## Deliverable

PR titled `feat(workflow-g): sttc connectivity + probabilistic thresholding + cli` with:

* CLI `--help`.
* Output filenames marked **public API**.
* The methodology section preview.
* One sample connectivity PNG attached.
* Tail of `pytest -q`.
* A note on the vectorization strategy used for `compute_sttc` (so reviewers can sanity-check it against the paper).
