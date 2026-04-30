# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to semantic versioning once the public API reaches 1.0.

## [Unreleased]

### Added

## [0.1.0] - 2026-04-30

### Added

- Bootstrapped the installable package skeleton, `meaorganoid` console entry point, `src/`
  layout, development configuration, and test structure.
- Added error classes `MEAValueError`, `MEASchemaError`, and `MEAQCError`.
- Added Workflow A ingestion for Axion spike CSV aliases and canonical `time_s`, `electrode`,
  and `well` event schemas.
- Added per-channel and per-well firing metrics with active-channel flags.
- Added Workflow B MaxInterval and logISI burst detection plus burst summary outputs.
- Added Workflow C baseline deltas, percent changes, paired Wilcoxon statistics, bootstrap CIs,
  and Holm correction.
- Added Workflow D NMT-style raster plots with optional burst overlays and firing-rate traces.
- Added Workflow E spatial firing-rate heatmaps over well electrode grids.
- Added Workflow F MEA-NAP-style group comparison tables and half-violin group plots.
- Added Workflow G STTC functional connectivity matrices, circular-shift probabilistic
  thresholding, network plots, and reusable NPZ outputs.
- Added Workflow H QC flags, QC summaries, and dashboard rendering.
- Added stable CLI subcommands for `process`, `batch`, `aggregate`, `plot`, `pipeline`,
  `compare-group`, `plot-group`, `connectivity`, `qc-report`, `bursts`, `compare-baseline`,
  `compare-conditions`, `plot-raster`, and `plot-spatial`.
- Added the MkDocs documentation site, generated CLI reference, API reference, per-workflow
  tutorials, methodology notes, changelog, and citation metadata.
- Added CI, coverage, pre-commit, release, docs-build, and local repository-health automation.
