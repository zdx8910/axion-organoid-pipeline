# Workflow E: Spatial Firing Heatmap

This tutorial uses `data/sample/workflow_e_channel_summary.csv` and renders one heatmap per well.

```bash
meaorganoid plot-spatial \
  --input data/sample/workflow_e_channel_summary.csv \
  --output-dir analysis_out \
  --prefix workflow_e \
  --global-scale
```

The command writes files named `<prefix>_spatial_heatmap_<well>.png`, for example:

| Output | Description |
|---|---|
| `workflow_e_spatial_heatmap_A1.png` | Spatial firing-rate heatmap for well `A1`. |
| `workflow_e_spatial_heatmap_B2.png` | Spatial firing-rate heatmap for well `B2`. |
