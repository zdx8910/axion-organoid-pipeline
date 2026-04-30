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
