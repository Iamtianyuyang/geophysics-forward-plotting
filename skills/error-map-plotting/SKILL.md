---
name: error-map-plotting
description: Plot a spatial residual/error map between a predicted array and a reference array — signed and relative errors use a diverging colormap with symmetric limits, absolute error uses a sequential colormap. Use when the user wants to quantify and visualize where one method differs from another or from ground truth.
---

# Skill: error-map-plotting

## Purpose

Plot spatial error maps between a predicted result and a reference result.
Used to quantify and visualize method accuracy in geophysical papers.

## When to Use

- You want to show residuals between two methods or between prediction and ground truth.
- You need to visualize where errors are large in physical space.
- You are writing a section on method accuracy or convergence.

## Inputs

| Parameter         | Type         | Description                                            |
|------------------|--------------|--------------------------------------------------------|
| `task_type`      | `"error_map"`| Required                                               |
| `data_paths`     | list[str]    | **Two** `.npy` files: `[predicted, reference]`         |
| `dx`             | float        | Horizontal spacing (km)                                |
| `dz`             | float        | Depth spacing (km)                                     |

Optional via `parameters`:
- `error_mode`: `"signed"` (default), `"absolute"`, or `"relative"`
- `cmap`: override default colormap

## Error Mode Details

| Mode        | Formula                     | Colormap          | Symmetric clim |
|-------------|-----------------------------|--------------------|----------------|
| `signed`    | `pred - ref`                | **Diverging**      | Yes            |
| `absolute`  | `|pred - ref|`              | **Sequential**     | No             |
| `relative`  | `(pred - ref) / |ref|`      | **Diverging**      | Yes            |

## Outputs

- `FigureResult.figure`: matplotlib Figure
- `FigureResult.saved_paths`: exported paths

## Geophysical Conventions

| Property          | Rule                                                         |
|-------------------|--------------------------------------------------------------|
| X axis label      | `Offset (km)` or `Distance (km)`                             |
| Y axis label      | `Time (s)` or `Depth (km)`                                   |
| Y direction       | **Downward**                                                 |
| Colorbar label    | `Signed Error`, `Absolute Error`, `Relative Error`, or `Residual (Pa)` |
| Signed colormap   | `seismic`, `RdBu_r`, or `bwr` (NEVER sequential)            |
| Absolute colormap | `viridis`, `hot`, or `afmhot` (NEVER diverging)             |
| Figure size       | 1.5 column: 5.5 × 4.0 in                                    |
| Font              | Times New Roman (serif), tick=10pt, label=11pt               |
| DPI               | 600                                                          |
| Export            | PDF (vector) + PNG (preview)                                 |

## Critical Rules

1. **Signed error MUST use a diverging colormap** — so zero-crossing is clearly at the color midpoint.
2. **Absolute error MUST use a sequential colormap** — it is non-negative by definition.
3. **Colorbar label must specify error type** — e.g., `Signed Error`, not just `Error`.
4. If using relative error, ensure denominator is never zero (handle near-zero reference values).

## Common Mistakes to Avoid

- Using a sequential colormap for signed error (hides sign of residual).
- Using a diverging colormap for absolute error (misleading).
- Omitting the error type from the colorbar label.
- Swapping the order of `pred` and `ref` arrays.

## Default Behavior

- Render image-like errors with `cigvis.plot2d` through the backend and pass
  physical x/y sampling, because CIGVis does not consume Matplotlib `extent`.
- error_mode: `signed`
- colormap: `seismic` (signed/relative), `viridis` (absolute)
- clim: symmetric (signed/relative), asymmetric (absolute), 99th percentile
- DPI: 600

## Example Prompt

```
Plot the signed error between method_a.npy (predicted) and method_b.npy (reference).
Both arrays are (nz=60, nx=120). dx=dz=0.025 km.
Use diverging colormap (seismic), symmetric clim.
Colorbar label: "Signed Error". Export as PNG and PDF.
```
