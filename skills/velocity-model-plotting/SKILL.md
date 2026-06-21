---
name: velocity-model-plotting
description: Plot a 2D seismic velocity model (nz×nx, in m/s or km/s) as a publication figure with a non-symmetric color scale, jet/turbo colormap, depth axis pointing down, and a mandatory velocity colorbar. Use when the user has a velocity model or any monotone spatial field to display.
---

# Skill: velocity-model-plotting

## Purpose

Plot seismic velocity models for geophysical publications.
This skill wraps CIGVis 2D image plotting with strict velocity-model conventions.

## When to Use

- You have a 2D or 3D velocity array (in m/s or km/s).
- You need a publication-grade velocity model figure.
- Input shape is typically `(nz, nx)` where z is depth and x is horizontal distance.

## Inputs

| Parameter       | Type              | Description                                 |
|----------------|-------------------|---------------------------------------------|
| `task_type`    | `"velocity_model"`| Required                                    |
| `data_paths`   | list[str]         | Path(s) to `.npy` velocity array            |
| `dx`           | float             | Horizontal sampling interval (km)           |
| `dz`           | float             | Vertical (depth) sampling interval (km)     |
| `x0`           | float             | Origin of x axis (km), default 0.0          |
| `z0`           | float             | Origin of z axis (km), default 0.0          |
| `title`        | str               | Figure title                                |
| `export_formats` | list[str]       | `["png", "pdf"]`                            |
| `dpi`          | int               | Default 600                                 |

Optional parameters via `parameters` dict:
- `cmap`: colormap name (default `"jet"`)
- Source/receiver marker positions (future extension)

## Outputs

- `FigureResult.figure`: matplotlib Figure
- `FigureResult.saved_paths`: list of exported file paths
- `FigureResult.review_messages`: any convention warnings

## Geophysical Conventions

| Property          | Value / Rule                                  |
|-------------------|-----------------------------------------------|
| X axis label      | `Distance (km)`                               |
| Y axis label      | `Depth (km)`                                  |
| Y direction       | **Downward** (depth increases downward)       |
| Colorbar label    | `Velocity (m/s)`                              |
| Colormap          | Non-symmetric; `jet` or `turbo` recommended   |
| Clim              | Asymmetric; based on actual velocity range    |

## Common Mistakes to Avoid

- **Do NOT** invert the y-axis to point upward — depth must go down.
- **Do NOT** use a diverging colormap (e.g., seismic/RdBu) for velocity models.
- **Do NOT** use array row indices as axis labels — use `km` coordinates.
- **Do NOT** omit the colorbar label (`Velocity (m/s)` is mandatory).
- **Do NOT** assume the array is `(nx, nz)` — standard is `(nz, nx)`.

## Default Behavior

- colormap: `jet`
- clim: asymmetric, 1st–99th percentile
- depth axis: downward
- DPI: 600
- Output formats: PNG

## Example Prompt

```
Plot the velocity model stored in velocity_model.npy.
Grid spacing: dx = dz = 0.025 km.
X axis: Distance (km). Y axis: Depth (km), pointing downward.
Colorbar label: Velocity (m/s). Use jet colormap.
Export as PNG (600 dpi) and PDF.
```

## CIGVis Reference

CIGVis provides 2D image plotting capabilities used by this skill.
See: https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-image
