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
