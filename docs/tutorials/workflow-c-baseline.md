# Workflow C: Baseline Normalization

This tutorial uses the sample well summary in `data/sample/workflow_c_well_summary.csv`.

## Delta From Baseline

```bash
meaorganoid compare-baseline \
  --input data/sample/workflow_c_well_summary.csv \
  --output-dir analysis_out \
  --prefix workflow_c \
  --baseline-label baseline
```

Example output:

| well | condition | mean_firing_rate_hz__delta | active_channel_count__delta |
|---|---|---:|---:|
| A1 | treatment | 0.5 | 1.0 |
| A2 | treatment | 0.5 | 1.0 |
| A3 | treatment | 0.5 | 1.0 |

## Paired Condition Stats

```bash
meaorganoid compare-conditions \
  --input data/sample/workflow_c_well_summary.csv \
  --output-dir analysis_out \
  --prefix workflow_c \
  --condition-a baseline \
  --condition-b treatment
```

Example output:

| metric | n_pairs | mean_a | mean_b | mean_diff |
|---|---:|---:|---:|---:|
| mean_firing_rate_hz | 6 | 1.5 | 2.0 | 0.5 |
| active_channel_count | 6 | 6.5 | 7.5 | 1.0 |
