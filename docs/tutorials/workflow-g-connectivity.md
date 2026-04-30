# Workflow G: Functional Connectivity

Workflow G computes STTC functional connectivity matrices from canonical spike events, thresholds
edges with circular-shift surrogates, and renders the network on the well electrode grid.

## Inputs

This tutorial uses the small sample files in `data/sample/`:

```text
data/sample/workflow_g_events.csv
data/sample/workflow_g_channel_summary.csv
data/sample/workflow_g_recording_manifest.csv
```

The event table must contain `time_s`, `electrode`, and `well`. The channel summary supplies node
colors and sizes through `mean_firing_rate_hz`. The recording manifest supplies
`recording_duration_s` per well.

## Run

```bash
meaorganoid connectivity \
  --input data/sample/workflow_g_events.csv \
  --channel-summary data/sample/workflow_g_channel_summary.csv \
  --manifest data/sample/workflow_g_recording_manifest.csv \
  --output-dir outputs/workflow_g \
  --prefix workflow_g \
  --n-iterations 50
```

## Outputs

The command writes one figure and one reusable matrix archive per well:

```text
outputs/workflow_g/workflow_g_connectivity_A1.png
outputs/workflow_g/workflow_g_connectivity_A1.npz
outputs/workflow_g/workflow_g_connectivity_B2.png
outputs/workflow_g/workflow_g_connectivity_B2.npz
```

The NPZ archive contains `adjacency`, `significance_mask`, `electrode_labels`, and `params`. These
keys are public API so downstream analysis can reuse the thresholded matrix without recomputing
circular-shift surrogates.
