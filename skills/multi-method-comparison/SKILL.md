---
name: multi-method-comparison
description: Compare 2–4 geophysical result arrays (shot records, wavefields, inversions) side by side in one figure with a single global color limit and one shared colorbar. Use when the user wants to compare methods, algorithms, or time steps and needs an apples-to-apples visual comparison.
---

# Skill: multi-method-comparison

## Purpose

Compare 2 to 4 geophysical results (shot records, wavefields, velocity inversions)
from different methods side by side in a single publication-grade figure.

## When to Use

- You have 2–4 result arrays from different modeling or inversion methods.
- You need to visually compare spatial or temporal differences.
- You are writing a paper section titled "Comparison of Methods" or similar.

## Inputs

| Parameter         | Type                        | Description                                             |
|------------------|-----------------------------|---------------------------------------------------------|
| `task_type`      | `"multi_method_comparison"` | Required                                                |
| `data_paths`     | list[str]                   | 2–4 `.npy` result arrays (same physical meaning)        |
| `method_names`   | list[str]                   | Labels for each panel (e.g. `["FD", "RTM", "FWI"]`)    |
| `dx`             | float                       | Horizontal spacing (km)                                 |
| `dz`/`dt`        | float                       | Vertical spacing (km or s)                              |
| `symmetric_clim` | bool                        | Recommended True for amplitude comparisons              |
| `clip_percentile`| float                       | Percentile for global clim, default 99.0                |
| `colorbar_label` | str                         | Shared colorbar label (e.g. `"Amplitude"`)              |

Optional via `parameters`:
- `cmap`: colormap name

## Outputs

- `FigureResult.figure`: multi-panel matplotlib Figure with one shared colorbar
- `FigureResult.saved_paths`: exported paths

## Geophysical Conventions

| Property              | Rule                                                             |
|-----------------------|------------------------------------------------------------------|
| Clim                  | **MUST be unified across all panels** (global percentile-based) |
| Colorbar              | **One shared colorbar** for the entire figure                   |
| Coordinate axes       | Identical extent across all panels                              |
| Colormap              | Same colormap for all panels                                    |
| Layout                | 1×N for ≤2 methods; 2×2 for 3–4 methods                        |

## Critical Rules — Read Carefully

### Rule 1: NEVER use independent per-panel normalization

Each panel MUST use the **same `vmin` / `vmax`** computed globally across all arrays.
Independent normalization makes all methods look equally "good" by stretching each
to its own range — this completely defeats the purpose of comparison.

**Wrong:**
```python
im1 = ax1.imshow(data_a, vmin=data_a.min(), vmax=data_a.max())  # WRONG
im2 = ax2.imshow(data_b, vmin=data_b.min(), vmax=data_b.max())  # WRONG
```

**Correct:**
```python
vmin, vmax = global_symmetric_clim([data_a, data_b], percentile=99)
im1 = ax1.imshow(data_a, vmin=vmin, vmax=vmax)
im2 = ax2.imshow(data_b, vmin=vmin, vmax=vmax)
```

### Rule 2: Use ONE shared colorbar

Do not add a colorbar to each subplot. Add a single shared colorbar using:
```python
fig.colorbar(last_im, ax=axes.ravel().tolist(), shrink=0.8)
```

### Rule 3: Align physical coordinates

All panels must use the same `extent` so spatial coordinates match visually.

## Common Mistakes to Avoid

- Per-panel independent normalization (the #1 mistake).
- Multiple colorbars (one per subplot).
- Different extents across panels (breaks spatial alignment).
- Method names missing or uninformative (e.g. "Method 1").
- Using more than 4 panels in a single row (unreadable on paper).

## Default Behavior

- Layout: 1×2 for 2 methods, 2×2 for 3–4 methods
- Clim: symmetric, global 99th percentile
- One shared colorbar on the right
- DPI: 600

## Example Prompt

```
Compare results from 4 methods: FD, RTM, LSRTM, FWI.
Data files: method_a.npy, method_b.npy, method_c.npy, method_d.npy.
All arrays are shape (nz=60, nx=120). dx=dz=0.025 km.
Use a 2x2 layout. Unified symmetric clim (99th percentile). One shared colorbar.
Labels: ["FD", "RTM", "LSRTM", "FWI"]. Export as PNG and PDF.
```
