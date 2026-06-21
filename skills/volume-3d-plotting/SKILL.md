---
name: volume-3d-plotting
description: Render a 3D seismic/velocity volume (nz×ny×nx) with CIGVis's vispy engine — multi-slice display plus optional fault, horizon, and well overlays. Use when the user has a 3D volume and a GUI/desktop environment; requires cigvis installed (raises a clear error otherwise).
---

# Skill: volume-3d-plotting

## Purpose

Render 3D seismic volume data using CIGVis's vispy-based 3D engine.
This skill wraps CIGVis 3D capabilities for geophysical forward-modeling volume output.

**Primary backend: CIGVis (vispy)**
See: https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-seismic-volume

CIGVis provides (refer to Gallery for full details):
- 3D seismic volume with multi-slice display
- fault overlay
- horizon overlay
- RGT (Relative Geologic Time) overlay
- well trajectory display
- point cloud overlay
- arbitrary line display
- axis display

## When to Use

- You have a 3D seismic volume array, shape `(nz, ny, nx)` or `(nx, ny, nz)`.
- You need to visualize cross-sections in X, Y, and Z simultaneously.
- You need to overlay faults, horizons, or well logs on the volume.
- You are using a GUI/desktop environment with vispy available.

## Inputs

| Parameter         | Type          | Description                                              |
|------------------|---------------|----------------------------------------------------------|
| `task_type`      | `"volume_3d"` | Required                                                 |
| `data_paths`     | list[str]     | Path to 3D `.npy` volume array                           |
| `symmetric_clim` | bool          | Default True for amplitude volumes                       |
| `clip_percentile`| float         | Default 99.0                                             |

Optional via `parameters`:
- `cmap`: colormap (default `"gray"`)
- `slices`: [i, j, k] — initial slice indices for X, Y, Z planes
- `fault_path`: str — path to fault overlay array
- `horizon_paths`: list[str] — horizon arrays to overlay

## Outputs

- `FigureResult.figure`: cigvis canvas (interactive 3D viewer)
- Note: no `saved_paths` by default (interactive display)

## Requirements

- **cigvis must be installed** (`pip install cigvis`)
- **vispy must be available** (requires GUI desktop environment)
- Does NOT work in headless CI/CD environments

## Fallback Behavior

If cigvis is not available, `BackendUnavailableError` is raised with a clear message.
In headless environments, use `sliceviewer` task type or extract 2D slices manually.

## Geophysical Conventions

| Axis     | Direction              |
|----------|------------------------|
| Z (depth)| Downward               |
| X, Y     | Positive direction →   |

## Common Mistakes to Avoid

- Confusing `(nz, ny, nx)` vs `(nx, ny, nz)` axis ordering.
- Running in headless environment without checking `cigvis_backend.is_available()`.
- Expecting a saved PNG - 3D viewer is interactive by default.

## Default Behavior

- Require CIGVis and a GUI-capable environment; never silently substitute a misleading 2D view.
- Initialize orthogonal slices near each axis center unless indices are provided.
- Use a 99th-percentile color limit and symmetric scaling for signed seismic amplitude.
- Return the interactive CIGVis canvas and save a static image only when explicitly requested.

## Example Prompt

```
Display the 3D seismic volume in volume_3d.npy using CIGVis.
Shape: (nz=30, ny=30, nx=60). Initial slices at [15, 15, 30].
Colormap: gray. Amplitude symmetric clim.
```

## CIGVis Gallery Reference

Refer to the CIGVis Gallery for all 3D features (fault/horizon/well overlays):
https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-seismic-volume
