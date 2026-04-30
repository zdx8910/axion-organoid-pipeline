# CLI

## `meaorganoid qc-report`

```text
Usage: meaorganoid qc-report [OPTIONS]

  Render a Workflow H QC dashboard and summary table.

Options:
  --input PATH            [required]
  --output-dir DIRECTORY  [required]
  --format [png|pdf]      [default: png]
  --help                  Show this message and exit.
```

## `meaorganoid bursts`

```text
Usage: meaorganoid bursts [OPTIONS]

  Detect Workflow B ISI bursts from canonical events.

Options:
  --input PATH                   [required]
  --output-dir DIRECTORY         [required]
  --prefix TEXT                  [required]
  --method [maxinterval|logisi]  [default: maxinterval]
  --max-isi-start-s FLOAT        [default: 0.17]
  --max-isi-end-s FLOAT          [default: 0.3]
  --min-ibi-s FLOAT              [default: 0.2]
  --min-burst-duration-s FLOAT   [default: 0.01]
  --min-spikes-in-burst INTEGER  [default: 3]
  --isi-threshold-s FLOAT
  --void-parameter FLOAT         [default: 0.7]
  --help                         Show this message and exit.
```

## `meaorganoid compare-baseline`

```text
Usage: meaorganoid compare-baseline [OPTIONS]

  Compute Workflow C within-well deltas from baseline.

Options:
  --input PATH            [required]
  --output-dir DIRECTORY  [required]
  --prefix TEXT           [required]
  --baseline-label TEXT   [required]
  --condition-col TEXT    [default: condition]
  --metrics TEXT          [default: mean_firing_rate_hz,active_channel_count]
  --help                  Show this message and exit.
```

## `meaorganoid compare-conditions`

```text
Usage: meaorganoid compare-conditions [OPTIONS]

  Compute Workflow C paired condition statistics.

Options:
  --input PATH            [required]
  --output-dir DIRECTORY  [required]
  --prefix TEXT           [required]
  --condition-a TEXT      [required]
  --condition-b TEXT      [required]
  --condition-col TEXT    [default: condition]
  --metrics TEXT          [default: mean_firing_rate_hz,active_channel_count]
  --help                  Show this message and exit.
```

## `meaorganoid compare-group`

```text
Usage: meaorganoid compare-group [OPTIONS]

  Compute Workflow F MEA-NAP-style group statistics and plots.

Options:
  --input PATH                    [required]
  --output-dir DIRECTORY          [required]
  --prefix TEXT                   [required]
  --group-col TEXT                [default: group]
  --metrics TEXT                  [default: mean_firing_rate_hz,active_channel
                                  _count,burst_rate_hz]
  --method [mannwhitneyu|kruskal]
                                  [default: mannwhitneyu]
  --correction [holm|bh|none]     [default: holm]
  --min-n-per-group INTEGER       [default: 3]
  --help                          Show this message and exit.
```

## `meaorganoid plot-raster`

```text
Usage: meaorganoid plot-raster [OPTIONS]

  Render Workflow D NMT-style raster plots.

Options:
  --input PATH            [required]
  --bursts-input PATH
  --output-dir DIRECTORY  [required]
  --prefix TEXT           [required]
  --well TEXT
  --time-window TEXT
  --bin-s FLOAT           [default: 1.0]
  --format [png|pdf|svg]  [default: png]
  --dpi INTEGER           [default: 150]
  --help                  Show this message and exit.
```

## `meaorganoid plot-spatial`

```text
Usage: meaorganoid plot-spatial [OPTIONS]

  Render Workflow E spatial firing heatmaps.

Options:
  --input PATH                    [required]
  --output-dir DIRECTORY          [required]
  --prefix TEXT                   [required]
  --well TEXT
  --metric TEXT                   [default: mean_firing_rate_hz]
  --grid-rows INTEGER             [default: 4]
  --grid-cols INTEGER             [default: 4]
  --global-scale / --per-well-scale
                                  [default: per-well-scale]
  --format [png|pdf|svg]          [default: png]
  --help                          Show this message and exit.
```

## `meaorganoid connectivity`

```text
Usage: meaorganoid connectivity [OPTIONS]

  Render Workflow G STTC functional connectivity networks.

Options:
  --input PATH            [required]
  --channel-summary FILE  [required]
  --manifest FILE         [required]
  --output-dir DIRECTORY  [required]
  --prefix TEXT           [required]
  --well TEXT
  --lag-s FLOAT           [default: 0.05]
  --n-iterations INTEGER  [default: 200]
  --percentile FLOAT      [default: 95.0]
  --min-spikes INTEGER    [default: 10]
  --seed INTEGER          [default: 0]
  --edge-threshold FLOAT  [default: 0.0]
  --format [png|pdf|svg]  [default: png]
  --help                  Show this message and exit.
```
