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
