---
name: sliceviewer-plotting
description: Launch CIGVis SliceViewer for interactive inline/crossline/depth browsing of one or more 3D seismic volumes. Use when the user wants to explore or quality-check a 3D dataset interactively in a notebook or desktop session; requires cigvis installed.
---

# Skill: sliceviewer-plotting

## Purpose

Launch CIGVis SliceViewer for interactive browsing of 3D seismic volumes.
Provides an interactive GUI where users can scrub through inline/crossline/depth slices.

**Primary backend: CIGVis SliceViewer**
See: https://cigvis.readthedocs.io/en/latest/gallery/index.html#sliceviewer

## When to Use

- You want to explore a 3D seismic dataset interactively.
- You need to compare multiple 3D volumes side by side in slices.
- You need to inspect data quality before plotting.

## Inputs

| Parameter         | Type            | Description                         |
|------------------|-----------------|-------------------------------------|
| `task_type`      | `"sliceviewer"` | Required                            |
| `data_paths`     | list[str]       | Path to 3D `.npy` volume array      |
| `symmetric_clim` | bool            | Default False (adjust to data)      |
| `clip_percentile`| float           | Default 99.0                        |

Optional via `parameters`:
- `cmap`: colormap (default `"gray"`)

## Outputs

- `FigureResult.figure`: cigvis viewer object
- Interactive window is launched; no file saved by default.

## Requirements

- **cigvis must be installed** with SliceViewer support
- Requires GUI desktop environment

## Fallback

If cigvis is unavailable, `BackendUnavailableError` is raised.
Use `volume_3d` or 2D slice extraction as alternatives.

## CIGVis Gallery Reference

CIGVis SliceViewer and comparison grid:
https://cigvis.readthedocs.io/en/latest/gallery/index.html#sliceviewer

Features available in CIGVis SliceViewer (refer to Gallery for details):
- Real seismic data slice viewer
- Real data comparison grid (multi-volume side-by-side)
- Colormap control
- Clim adjustment

## Geophysical Conventions

- Confirm volume axis order before opening; do not infer inline/crossline/depth labels blindly.
- Keep compared volumes on identical slice indices, extents, units, colormap, and color limits.
- Point depth coordinates downward and display physical coordinates when metadata is available.
- Use symmetric limits for signed amplitudes and sequential limits for positive properties.

## Common Mistakes to Avoid

- Launching an interactive viewer in headless CI or a remote session without display support.
- Comparing volumes with different grids or independent color limits.
- Confusing `(nz, ny, nx)` with the layout expected by the installed CIGVis version.
- Treating an exploratory screenshot as a publication export without figure review.

## Default Behavior

- Require CIGVis and fail with an actionable error when unavailable.
- Use the 99th percentile for initial clipping and `gray` as the default colormap.
- Open synchronized slices for comparison when compatible volumes are supplied.
- Return the viewer object; do not claim a static file export unless explicitly saved.

## Example Prompt

```
Launch CIGVis SliceViewer for volume_3d.npy.
Shape (nz=30, ny=30, nx=60). Colormap: gray. Clim auto from 99th percentile.
```
