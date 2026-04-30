# Methodology

This page defines the calculations and defaults behind the eight public workflows. Output
filenames, output columns, and QC flag names are public API.

## Workflow A: Ingestion

Workflow A reads Axion spike CSV exports after spike detection. Column aliases are matched
case-insensitively after trimming whitespace.

| Canonical column | Accepted aliases |
|---|---|
| `time_s` | `Time (s)`, `Time`, `Timestamp`, `Spike Time`, `SpikeTime`, `time_s` |
| `electrode` | `Electrode`, `Channel`, `Electrode Name`, `Channel Label` |
| `well` | `Well`, `Well Label`, `Well ID`, `WellName` |

If `well` is missing, labels like `A1_11` are used to infer the well prefix. Required missing
columns raise `MEASchemaError`; the parser never silently guesses a time or electrode column.

Per-channel firing rate is:

```text
firing_rate_hz = spike_count / recording_duration_s
```

Active channels use `active_threshold_hz = 0.1` by default.

## Workflow B: ISI-Based Burst Detection

Workflow B detects single-electrode bursts from canonical spike events. It does not detect network
bursts.

### MaxInterval

The MaxInterval detector follows the Legéndy and Salcman (1985) / Cocatre-Zilgien and Delcomyn
(1992) family of ISI rules. Candidate bursts start when at least one adjacent-spike interval is at
or below `max_isi_start_s`, extend while intervals remain at or below `max_isi_end_s`, and merge
adjacent candidates when their inter-burst interval is below `min_ibi_s`. Candidates are retained
only when they meet `min_burst_duration_s` and `min_spikes_in_burst`.

Defaults: `max_isi_start_s = 0.170`, `max_isi_end_s = 0.300`, `min_ibi_s = 0.200`,
`min_burst_duration_s = 0.010`, and `min_spikes_in_burst = 3`.

### logISI

The logISI detector follows Pasquale et al. (2010). When `isi_threshold_s` is provided, adjacent
spikes separated by ISIs at or below that threshold are grouped into bursts. When
`isi_threshold_s` is omitted, the threshold is derived from a smoothed histogram of `log10(ISI)`
values. The first trough between two log-ISI peaks is accepted when its void parameter, defined as
the trough depth relative to the smaller surrounding peak, is at least `void_parameter`.

Defaults: `isi_threshold_s = None`, `min_spikes_in_burst = 3`, and `void_parameter = 0.7`.

### Burst Output Schemas

`<prefix>_bursts.csv` columns: `well`, `electrode`, `burst_index`, `start_s`, `end_s`,
`duration_s`, `n_spikes`, `mean_isi_s`, `intra_burst_rate_hz`, `method`.

`<prefix>_burst_summary.csv` columns: `well`, `electrode`, `n_bursts`,
`mean_burst_duration_s`, `mean_intra_burst_rate_hz`, `mean_ibi_s`, `burst_rate_hz`,
`percent_spikes_in_bursts`.

## Workflow C: Baseline Normalization

Workflow C computes within-well deltas from a baseline condition:

```text
delta = condition_value - baseline_value
pct_change = 100 * delta / baseline_value
```

Paired condition statistics use a two-sided Wilcoxon signed-rank test per metric, bootstrap
confidence intervals on paired differences, and Holm correction across metrics. Wells without a
baseline row are logged and excluded.

## Workflow D: Raster Plot

Workflow D renders NMT-style spike rasters by well. Spike events are sorted by natural electrode
label, optionally clipped to a user-provided time window, and paired with a population firing-rate
trace. The default firing-rate bin size is `bin_s = 1.0`.

## Workflow E: Spatial Heatmap

Workflow E maps channel metrics onto a rectangular electrode grid. Electrode labels must follow the
`<well>_<row><col>` convention, such as `A1_11`. The default grid shape is `(4, 4)`. Inactive
channels are hatched when an `active` or `is_active` column is present.

## Workflow F: Group Comparison

Workflow F compares well-level metrics across experimental groups. The default metrics are
`mean_firing_rate_hz`, `active_channel_count`, and `burst_rate_hz`.

Two retained groups use a two-sided Mann-Whitney U test. Three or more retained groups use
Kruskal-Wallis rank comparison and pairwise Dunn-style rank tests. Groups with fewer than
`min_n_per_group = 3` rows are dropped with an INFO log message. P-values are corrected across all
rows by Holm correction by default; Benjamini-Hochberg and no correction are also available.

The public output schema is:

```text
metric,group_a,group_b,n_a,n_b,median_a,median_b,statistic,p_raw,p_adj,significant,effect_size_r
```

## Workflow G: STTC Functional Connectivity

Workflow G computes functional connectivity with the Spike Time Tiling Coefficient (STTC; Cutts
and Eglen, 2014). For two spike trains A and B, `PA` is the proportion of spikes in A within
`lag_s` of any spike in B, and `PB` is the matching proportion for spikes in B. `TA` and `TB` are
the fractions of recording time covered by the union of all `± lag_s` windows around spikes in A
and B. The coefficient is:

```text
STTC = 0.5 * ((PA - TB) / (1 - PA * TB) + (PB - TA) / (1 - PB * TA))
```

The default lag is `lag_s = 0.05` seconds. Electrodes with fewer than `min_spikes = 10` spikes are
excluded before matrix construction, following the MEA-NAP convention of removing very sparse
channels from network statistics.

Edges are thresholded with circular-shift null distributions. For each electrode pair, one train is
shifted by random offsets modulo the recording duration, STTC is recomputed for each surrogate, and
the real edge is retained only when it exceeds the pair-specific `percentile = 95.0` null cutoff.
The default number of surrogates is `n_iterations = 200`.

The NPZ output contains `adjacency`, `significance_mask`, `electrode_labels`, and `params`.

## Workflow H: QC Report

Workflow H adds these public QC columns to recording manifests and well summaries.

| Flag | Definition | Formula | Default threshold | Data type |
|---|---|---|---|---|
| `qc_low_active_channels` | Recording has too few active channels for reliable downstream analysis. | `active_channel_count < min_active_channels`. | `min_active_channels = 4` active channels. | boolean |
| `qc_short_duration` | Recording is shorter than the minimum duration expected for stable summary metrics. | `recording_duration_s < min_duration_s`. | `min_duration_s = 60.0` seconds. | boolean |
| `qc_outlier_rate` | Recording mean firing rate is an outlier relative to recordings in the same group. | Absolute z-score of `mean_firing_rate_hz` within `condition` is greater than `outlier_rate_z`; groups with zero variance are not flagged. | `outlier_rate_z = 3.0` within `condition`. | boolean |
| `qc_status` | Overall QC status for the row. | `"pass"` when no boolean QC flag is true, otherwise `"fail"`. | Derived from the three boolean QC flags. | string |
| `qc_reasons` | Machine-readable list of failing QC flags. | Comma-joined failing flag names in stable order: low active channels, short duration, outlier rate; empty string when passing. | Derived from the three boolean QC flags. | string |

The QC dashboard summarizes pass/fail counts, failure reasons, recording durations, and
active-channel counts.
