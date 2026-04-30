# Methodology

## QC flags

Workflow H adds these public QC columns to recording manifests and well summaries.

| Flag | Definition | Formula | Default threshold | Data type |
|---|---|---|---|---|
| `qc_low_active_channels` | Recording has too few active channels for reliable downstream analysis. | `active_channel_count < min_active_channels`. | `min_active_channels = 4` active channels. | boolean |
| `qc_short_duration` | Recording is shorter than the minimum duration expected for stable summary metrics. | `recording_duration_s < min_duration_s`. | `min_duration_s = 60.0` seconds. | boolean |
| `qc_outlier_rate` | Recording mean firing rate is an outlier relative to recordings in the same group. | Absolute z-score of `mean_firing_rate_hz` within `condition` is greater than `outlier_rate_z`; groups with zero variance are not flagged. | `outlier_rate_z = 3.0` within `condition`. | boolean |
| `qc_status` | Overall QC status for the row. | `"pass"` when no boolean QC flag is true, otherwise `"fail"`. | Derived from the three boolean QC flags. | string |
| `qc_reasons` | Machine-readable list of failing QC flags. | Comma-joined failing flag names in stable order: low active channels, short duration, outlier rate; empty string when passing. | Derived from the three boolean QC flags. | string |

## ISI-based burst detection

Workflow B detects single-electrode bursts from canonical spike events. It does not detect network bursts.

### MaxInterval

The MaxInterval detector follows the Legéndy and Salcman (1985) / Cocatre-Zilgien and Delcomyn (1992) family of ISI rules. Candidate bursts start when at least one adjacent-spike interval is at or below `max_isi_start_s`, extend while intervals remain at or below `max_isi_end_s`, and merge adjacent candidates when their inter-burst interval is below `min_ibi_s`. Candidates are retained only when they meet `min_burst_duration_s` and `min_spikes_in_burst`.

Defaults: `max_isi_start_s = 0.170`, `max_isi_end_s = 0.300`, `min_ibi_s = 0.200`, `min_burst_duration_s = 0.010`, and `min_spikes_in_burst = 3`.

### logISI

The logISI detector follows Pasquale et al. (2010). When `isi_threshold_s` is provided, adjacent spikes separated by ISIs at or below that threshold are grouped into bursts. When `isi_threshold_s` is omitted, the threshold is derived from a smoothed histogram of `log10(ISI)` values: the first trough between two log-ISI peaks is accepted when its void parameter, defined as the trough depth relative to the smaller surrounding peak, is at least `void_parameter`.

Defaults: `isi_threshold_s = None`, `min_spikes_in_burst = 3`, and `void_parameter = 0.7`.

### Burst Output Schemas

`<prefix>_bursts.csv` columns: `well`, `electrode`, `burst_index`, `start_s`, `end_s`, `duration_s`, `n_spikes`, `mean_isi_s`, `intra_burst_rate_hz`, `method`.

`<prefix>_burst_summary.csv` columns: `well`, `electrode`, `n_bursts`, `mean_burst_duration_s`, `mean_intra_burst_rate_hz`, `mean_ibi_s`, `burst_rate_hz`, `percent_spikes_in_bursts`.

## STTC functional connectivity

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

Workflow G output filenames are public API:

```text
<prefix>_connectivity_<well>.<fmt>
<prefix>_connectivity_<well>.npz
```

The NPZ contains `adjacency`, `significance_mask`, `electrode_labels`, and `params`.
