---
name: wavefield-snapshot-plotting
description: Plot an instantaneous 2D wavefield snapshot (nz×nx at a fixed time step) with symmetric color limits, a diverging colormap, depth axis down, and an optional "t = X.XXX s" time annotation. Use when the user wants to visualize wave propagation at a single simulation time.
---

# Skill: wavefield-snapshot-plotting

## Purpose

Plot instantaneous wavefield snapshots from forward-modeling simulations.
Each snapshot is a 2D spatial field at a fixed time step.

## When to Use

- You have a 2D wavefield array `(nz, nx)` representing a single time step.
- You want to visualize wave propagation in a velocity model domain.
- You need to annotate the snapshot with its simulation time.

## Inputs

| Parameter         | Type                   | Description                                   |
|------------------|------------------------|-----------------------------------------------|
| `task_type`      | `"wavefield_snapshot"` | Required                                      |
| `data_paths`     | list[str]              | Path(s) to `.npy` snapshot array(s)           |
| `dx`             | float                  | Horizontal spacing (km)                       |
| `dz`             | float                  | Depth spacing (km)                            |
| `x0`             | float                  | Origin of x axis (km)                         |
| `z0`             | float                  | Origin of z axis (km)                         |
| `symmetric_clim` | bool                   | **Should be True** (default True)             |
| `clip_percentile`| float                  | Percentile for clim, default 99.0             |

Optional via `parameters`:
- `snapshot_time`: float (seconds) — annotated as `t = X.XXX s` on the figure
- `cmap`: colormap (default `"seismic"`)

## Outputs

- `FigureResult.figure`: matplotlib Figure with optional time annotation
- `FigureResult.saved_paths`: exported file paths

## Geophysical Conventions

| Property          | Value / Rule                                          |
|-------------------|-------------------------------------------------------|
| X axis label      | `Distance (km)`                                       |
| Y axis label      | `Depth (km)`                                          |
| Y direction       | **Downward** (depth increases downward)               |
| Colorbar label    | `Pressure (Pa)`                                       |
| Colormap          | Diverging: `seismic` or `RdBu_r`                      |
| Clim              | **Symmetric** `[-v, +v]`                              |
| Figure size       | Single column: 3.5 × 2.8 in                          |
| Font              | Times New Roman (serif), tick=10pt, label=11pt        |
| DPI               | 600                                                   |
| Export            | PDF (vector) + PNG (preview)                          |

## Critical Rules

1. **Depth axis MUST point downward** — z=0 is the surface at the top.
2. **Amplitude MUST use symmetric clim** — wavefield has equal positive/negative.
3. **Snapshot time annotation is strongly recommended** — helps readers understand propagation stage.
4. Physical coordinates (km), not grid indices, must label both axes.

## Common Mistakes to Avoid

- Depth axis pointing upward.
- Using non-symmetric or sequential colormap for wavefield amplitude.
- Forgetting to annotate snapshot time (readers cannot understand the propagation stage).
- Plotting raw amplitude without clipping (outliers collapse the color range).

## Default Behavior

- Render with `cigvis.plot2d` through the backend after normalizing to `(nz, nx)`.
- Verify CIGVis preserved the spatial axes before adding the time annotation.
- colormap: `seismic`
- symmetric_clim: `True`
- clip_percentile: 99.0
- snapshot_time annotation: added if `parameters["snapshot_time"]` is set
- DPI: 600

## Example Prompt

```
Plot the wavefield snapshot at t=0.3 s from wavefield_snapshot.npy.
Shape is (nz=60, nx=120). dx=dz=0.025 km.
X axis: Distance (km). Y axis: Depth (km), pointing downward.
Use symmetric seismic colormap. Annotate "t = 0.300 s" in the lower-left corner.
Export as PNG (600 dpi).
```

## CIGVis Reference

CIGVis 2D image plotting supports this kind of spatial field visualization.
```python
import cigvis
cigvis.plot2d(snap, cmap='seismic', clim=[-v, v], cbar='Pressure (Pa)',
              xlabel='Distance (km)', ylabel='Depth (km)', ax=ax)
```
See: https://cigvis.readthedocs.io/en/latest/gallery/index.html#2d
