# Quickstart

This quickstart runs a small Axion-style spike CSV through Workflow A and produces channel and
well summaries. It is the fastest way to confirm the package, CLI, and sample data are working.

## Inputs

```text
data/sample/workflow_a_axion_spikes.csv
```

```python
import pandas as pd

spikes = pd.read_csv("data/sample/workflow_a_axion_spikes.csv")
spikes.head()
```

## Run

```bash
meaorganoid process \
  --input data/sample/workflow_a_axion_spikes.csv \
  --output-dir outputs/quickstart \
  --prefix quickstart
```

## Outputs

The command writes tidy CSVs and JSON metadata:

```text
outputs/quickstart/quickstart_channel_summary.csv
outputs/quickstart/quickstart_well_summary.csv
outputs/quickstart/quickstart_run_metadata.json
outputs/quickstart/quickstart_input_metadata.json
```

```python
well_summary = pd.read_csv("outputs/quickstart/quickstart_well_summary.csv")
well_summary[["well", "active_channel_count", "mean_firing_rate_hz"]]
```

![Quickstart well summary](../assets/workflows/workflow-a-event-counts.png)

!!! note "Public API"
    Stable output filenames: `<prefix>_channel_summary.csv`,
    `<prefix>_well_summary.csv`, `<prefix>_run_metadata.json`, and
    `<prefix>_input_metadata.json`.
