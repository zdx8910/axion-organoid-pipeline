# Workflow D: NMT-Style Raster Plot

This tutorial uses `data/sample/workflow_d_events.csv` and renders one raster per well.

```bash
meaorganoid plot-raster \
  --input data/sample/workflow_d_events.csv \
  --output-dir analysis_out \
  --prefix workflow_d \
  --format png
```

The command writes files named `<prefix>_raster_<well>.png`, for example:

| Output | Description |
|---|---|
| `workflow_d_raster_A1.png` | Raster and population firing-rate trace for well `A1`. |
| `workflow_d_raster_A2.png` | Raster and population firing-rate trace for well `A2`. |
