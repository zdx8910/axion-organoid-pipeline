# Workflow F: Group Comparison

Workflow F compares well-level metrics across experimental groups and writes one tidy statistics
table plus one MEA-NAP-style group plot per metric.

## Inputs

Start from an aggregated well summary table with one row per well or recording. The table must
include the grouping column and each metric you want to test.

```text
data/sample/workflow_f_well_summary.csv
```

Required columns for this tutorial:

- `group`
- `mean_firing_rate_hz`
- `active_channel_count`
- `burst_rate_hz`

## Run

```bash
meaorganoid compare-group \
  --input data/sample/workflow_f_well_summary.csv \
  --output-dir outputs/workflow_f \
  --prefix workflow_f \
  --group-col group \
  --metrics mean_firing_rate_hz,active_channel_count,burst_rate_hz
```

## Outputs

The command writes:

```text
outputs/workflow_f/workflow_f_group_comparison.csv
outputs/workflow_f/workflow_f_group_comparison_mean_firing_rate_hz.png
outputs/workflow_f/workflow_f_group_comparison_active_channel_count.png
outputs/workflow_f/workflow_f_group_comparison_burst_rate_hz.png
```

The CSV schema is public API:

```text
metric,group_a,group_b,n_a,n_b,median_a,median_b,statistic,p_raw,p_adj,significant,effect_size_r
```

With two retained groups, Workflow F uses a two-sided Mann-Whitney U test. With three or more
retained groups, it performs a Kruskal-Wallis rank comparison and reports pairwise Dunn-style
rank tests. P-values are adjusted across all rows using Holm correction by default.
