# mea-organoid-toolkit

A lightweight, CSV-first analysis toolkit for Axion microelectrode array (MEA) recordings of brain
organoids.

`meaorganoid` formalizes the glue layer between Axion spike CSV exports, NMT-style figures,
MEA-NAP-style group analysis, and reproducible Python workflows. It does not replace AxIS, NMT, or
MEA-NAP. It bridges them with a single tested package and stable CLI.

## Install

```bash
pip install meaorganoid
```

For development:

```bash
git clone https://github.com/zdx8910/axion-organoid-pipeline
cd axion-organoid-pipeline
pip install -e ".[dev,docs]"
```

## Workflows

| ID | Workflow | Module |
|---|---|---|
| A | Ingestion: Axion CSV to tidy events | `meaorganoid.io` |
| B | ISI-based burst detection | `meaorganoid.bursts` |
| C | Baseline normalization | `meaorganoid.compare` |
| D | NMT-style raster plot | `meaorganoid.plot.raster` |
| E | Spatial firing heatmap | `meaorganoid.plot.spatial` |
| F | MEA-NAP-style group comparison | `meaorganoid.compare.group` |
| G | STTC functional connectivity | `meaorganoid.connectivity` |
| H | QC report | `meaorganoid.qc` |

Start with the [Quickstart](tutorials/quickstart.md), then move through the workflow tutorials.
