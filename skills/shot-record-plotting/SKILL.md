---
name: shot-record-plotting
description: Plot a seismic shot record / common-shot gather (nt×nx) with forced symmetric color limits, a diverging seismic colormap, time axis pointing down, and physical receiver coordinates. Use when the user has 2D seismic amplitude data from forward modeling and wants a publication-grade gather figure.
---

# Skill: shot-record-plotting

## Purpose

Plot seismic shot records (common-shot gathers) for geophysical publications.
This is one of the most common forward-modeling output figures.

## When to Use

- You have a 2D shot record array, shape `(nt, nx)`.
- You need to compare multiple shot records with **unified amplitude scaling**.
- You need a publication-grade figure with time axis pointing downward.

## Inputs

| Parameter         | Type              | Description                                      |
|------------------|-------------------|--------------------------------------------------|
| `task_type`      | `"shot_record"`   | Required                                         |
| `data_paths`     | list[str]         | Path(s) to `.npy` shot record arrays             |
| `dt`             | float             | Time sampling interval (s), e.g. 0.002           |
| `dx`             | float             | Receiver spacing (km)                            |
| `x0`             | float             | First receiver position (km)                     |
| `t0`             | float             | Start time (s), default 0.0                      |
| `symmetric_clim` | bool              | **Should be True** (default True)                |
| `clip_percentile`| float             | Percentile for clim, default 99.0                |
| `export_formats` | list[str]         | `["png", "pdf"]`                                 |

Optional via `parameters`:
- `cmap`: colormap (default `"seismic"` or `"gray"`)

## Outputs

- `FigureResult.figure`: matplotlib Figure
- `FigureResult.saved_paths`: exported file paths
- `FigureResult.review_messages`: convention warnings

## Geophysical Conventions

| Property          | Value / Rule                                          |
|-------------------|-------------------------------------------------------|
| X axis label      | `Offset (km)`                                         |
| Y axis label      | `Time (s)`                                            |
| Y direction       | **Downward** (time increases downward)                |
| Colorbar label    | `Amplitude`                                           |
| Colormap          | Diverging: `seismic` or `gray`                        |
| Clim              | **Symmetric** `[-v, +v]` based on percentile         |
| Multi-panel clim  | **Unified across all panels** — NEVER independent     |
| Figure size       | 1.5 column: 5.5 × 4.0 in                             |
| Font              | Times New Roman (serif), tick=10pt, label=11pt        |
| DPI               | 600                                                   |
| Export            | PDF (vector) + PNG (preview)                          |

## Critical Rules (enforce strictly)

1. **Time axis MUST point downward.** If the array is `(nt, nx)`, row 0 is t=0 at the top.
2. **Amplitude color scale MUST be symmetric** (`symmetric_clim=True`).
   A non-symmetric scale distorts the visual balance of positive/negative amplitudes.
3. **When comparing multiple shot records, ALL panels MUST use the same clim.**
   Independent normalization makes amplitude comparisons meaningless.
4. **Use physical receiver coordinates, not receiver index**, for the x axis.

## Common Mistakes to Avoid

- Setting `symmetric_clim=False` — always use symmetric for amplitude.
- Each subplot having its own clim — creates false visual differences.
- Plotting `data.T` (transposed) when the array is already `(nt, nx)`.
- Using sequential colormaps (e.g., viridis) for amplitude — must be diverging.
- Labeling x axis as "Trace" or "Index" instead of physical distance.

## Default Behavior

- colormap: `seismic`
- symmetric_clim: `True`
- clip_percentile: 99.0
- Y direction: downward
- DPI: 600

## Example Prompt

```
Plot the shot record in shot_record.npy.
Shape is (nt=500, nx=120). dt=0.002 s, dx=0.025 km.
X axis: Receiver position (km). Y axis: Time (s), pointing downward.
Use symmetric amplitude colormap (seismic), clim based on 99th percentile.
Export as PNG (600 dpi).
```

## CIGVis Reference

CIGVis provides 2D image and 1D seismogram plotting used by this skill.
See: https://cigvis.readthedocs.io/en/latest/gallery/index.html
