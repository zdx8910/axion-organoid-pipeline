# axion-organoid-pipeline

A lightweight, CSV-first analysis toolkit for Axion microelectrode array (MEA) recordings of brain organoids.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## What this is

Most organoid MEA labs glue together four things by hand: **AxIS** (Axion's acquisition software), **NMT** exports (raster plots and per-recording metrics), **MEA-NAP** (MATLAB-based group analysis), and **ad-hoc Python** scripts. The result is reproducibility loss, integration tax, and Methods sections that cite "custom scripts."

`meaorganoid` formalizes that glue layer as a single, tested, pip-installable Python package with a stable CLI. It does not replace AxIS, NMT, or MEA-NAP — it bridges them.

It starts from Axion spike CSV exports (post-detection) and produces:

- Per-channel and per-well firing summaries with explicit QC flags
- Baseline-normalized condition comparisons
- NMT-style raster figures, spatial firing heatmaps, connectivity networks
- MEA-NAP-style group comparisons across many recordings
- Tidy outputs ready for downstream stats

## Install

```bash
pip install meaorganoid
```

Or from source:

```bash
git clone https://github.com/zdx8910/axion-organoid-pipeline
cd axion-organoid-pipeline
pip install -e ".[dev]"
```

## Quickstart

Run the full pipeline against a folder of Axion spike CSVs:

```bash
meaorganoid pipeline \
  --input-dir path/to/spike_csv_folder \
  --output-dir analysis_out \
  --pattern "*_spike_list.csv" \
  --combined-prefix experiment_combined
```

See [`docs/tutorials/quickstart.md`](docs/tutorials/quickstart.md) for a step-by-step walkthrough using the included sample dataset.

## Workflows

Every paper figure maps to one of these eight reference workflows:

| ID | Workflow                                  | Module                          |
|----|-------------------------------------------|---------------------------------|
| A  | Ingestion (Axion CSV → tidy events)        | `meaorganoid.io`                |
| B  | ISI-based burst detection                  | `meaorganoid.bursts`            |
| C  | Baseline normalization (within-well delta) | `meaorganoid.compare`           |
| D  | NMT-style raster plot                      | `meaorganoid.plot.raster`       |
| E  | Spatial firing heatmap                     | `meaorganoid.plot.spatial`      |
| F  | MEA-NAP-style group comparison             | `meaorganoid.compare.group`     |
| G  | Functional connectivity network            | `meaorganoid.connectivity`      |
| H  | QC dashboard                               | `meaorganoid.qc`                |

## Citation

If you use `meaorganoid` in published work, please cite:

> *(Manuscript in preparation; preprint forthcoming on bioRxiv. See `CITATION.cff` for software citation metadata.)*

## Contributing

This project uses an `AGENTS.md` file at the repo root that defines conventions and scope. Read it before opening a PR. Style: `ruff format`, `ruff check`, `mypy --strict`, `pytest -q` must all pass.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

This work builds on conventions established by Axion BioSystems' AxIS and Neural Metric Tool, and by the MEA-NAP project. It is independent of and not endorsed by either.
