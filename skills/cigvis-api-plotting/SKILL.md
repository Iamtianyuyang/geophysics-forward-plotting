---
name: cigvis-api-plotting
description: Select and apply public CIGVis APIs for geophysical 1D, 2D, 3D VisPy, browser-based Viser, Plotly/Jupyter, and SliceViewer rendering. Use for any seismic plotting task that should prefer CIGVis, especially when axis order, slice direction, overlays, horizons, faults, wells, bodies, point clouds, splats, or interactive browsing are involved.
---

# CIGVis API Plotting

## Purpose

Choose the smallest public CIGVis API that satisfies a geophysical plotting
request. Preserve this framework's physical-axis contract while delegating
rendering to CIGVis instead of recreating its visualization primitives.

## When to Use

- Use after the root `geophysics-forward-plotting` router for every 1D, 2D, or
  3D geophysical view.
- Use before modifying `CigvisBackend` or writing direct CIGVis calls.
- Use when adding faults, RGT, horizons, wells, bodies, points, arbitrary lines,
  point clouds, splats, colorbars, axes, or linked comparisons.
- Use when a plot is transposed, mirrored, upside down, or labeled with the
  wrong physical dimension.

## Inputs

- NumPy arrays or `.npy` paths.
- An explicit data layout such as `nt_nx`, `nz_nx`, `nz_ny_nx`, or `nx_ny_nz`.
- Physical sampling and origins (`dx`, `dy`, `dz`, `dt`, `x0`, `y0`, `z0`, `t0`).
- A rendering target: static 2D, VisPy desktop 3D, Viser browser 3D,
  Plotly/Jupyter 3D, or SliceViewer.
- Optional overlay arrays and their colormap, alpha, level, or point metadata.

## Outputs

- A selected public CIGVis API route.
- CIGVis nodes, a Matplotlib Figure returned by CIGVis 1D/2D helpers, a 3D
  canvas/server, or SliceViewer nodes/server.
- Explicit axis-order conversion and a verification record.
- An actionable dependency error when the requested optional CIGVis backend is
  unavailable.

## Workflow

1. Inspect `shape`, declared layout, units, and physical meaning before plotting.
2. Read [axis-order.md](references/axis-order.md) whenever data has two or more
   dimensions. Do not infer 3D order from shape alone.
3. Select an API family from [api-routing.md](references/api-routing.md).
4. Read [recipes.md](references/recipes.md) only for the selected API family.
5. Inside this repository, call `geophysics_forward_plotting.backend.cigvis_backend`
   rather than duplicating order conversion or optional-dependency handling.
6. Use Matplotlib only for performance/statistical plots or when the 2D CIGVis
   dependency is unavailable.
7. Verify rendered shape, axis direction, physical ticks, color normalization,
   and overlay alignment before export.

## API Selection

| Request | Preferred CIGVis API |
|---|---|
| One trace | `cigvis.plot1d` |
| Wiggle/wigb gather | `cigvis.plot_multi_traces` |
| 2D model, record, snapshot, error | `cigvis.plot2d` |
| 2D mask/fault/RGT | `fg_image_args` plus `plot2d(..., fg=...)` |
| 2D line/source/receiver annotation | `line_args`, `marker_args`, `annotate_args` |
| Desktop 3D slices | `create_slices` plus `plot3D` |
| 3D mask/RGT/fault | `add_mask` |
| Horizon/body/well/picks | `create_surfaces`, `create_bodies`, `create_well_logs`, `create_points` |
| Browser 3D | `cigvis.viserplot` |
| Interactive 2D slice browser | `cigvis.sliceviewer.create_slice` plus `show` |

## Geophysical Conventions

- Normalize static 2D data to `(vertical, horizontal)` before calling the
  backend: `(nt, nx)` or `(nz, nx)`.
- Normalize desktop/browser 3D data to CIGVis line-first `(x, y, z/time)` only
  at the backend boundary.
- Keep SliceViewer arrays in their declared native layout and set
  `display_axes=(y_axis, x_axis)` explicitly.
- Time and depth increase downward in 2D figures.
- Signed amplitude uses symmetric limits and a diverging colormap.
- Compared panels share one global color range and physical extent.
- Apply exactly the same transform to a 3D mask as to its base volume.

## Common Mistakes to Avoid

- Calling raw `cigvis.plot2d` on `(nz, nx)` while global `LINE_FIRST=True`;
  CIGVis will transpose it.
- Passing `(nz, ny, nx)` directly to APIs documented for `(x, y, z)`.
- Copying the obsolete `sliceviewer.SliceViewer(...)` pattern. Current examples
  use `create_slice`, optional `add_mask`/annotations, then `show`.
- Wrapping `fg_image_args` or `marker_args` in another list; these helpers
  already return the list expected by `fg`.
- Catching every CIGVis exception and silently falling back. Fallback is for an
  unavailable 2D dependency, not for malformed CIGVis calls.
- Using Viser when a static file is required without planning browser capture.

## Default Behavior

- Prefer CIGVis for geophysical traces, images, volumes, and viewers.
- Use VisPy for desktop 3D, Viser for browser 3D, and SliceViewer for remote
  slice exploration.
- Preserve and restore CIGVis global order settings around adapter calls.
- Add a CIGVis axis node and colorbar to 3D scenes unless explicitly disabled.
- Require an explicit `data_layout` when metadata and shape cannot establish
  the axis meaning safely.

## Verification

- For a 2D input `(nv, nh)`, assert the rendered image array is `(nv, nh)`.
- Assert `ax.get_ylim()[0] > ax.get_ylim()[1]` for time/depth-down plots.
- For `nz_ny_nx`, assert CIGVis receives `(nx, ny, nz)` and converted slice
  positions.
- Assert multi-panel images use identical `clim`.
- Assert masks/surfaces align with the converted base volume.
- Assert CIGVis global order is restored after the call.

## Example Prompt

```text
Use $cigvis-api-plotting to render a wavefield volume declared as nz_ny_nx.
Use CIGVis VisPy slices with a fault mask, a horizon surface, physical axis
sampling, symmetric amplitude limits, and verify that depth points downward.
```
