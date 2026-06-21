---
name: volume-3d-plotting
description: Render 3D seismic, velocity, or wavefield volumes with CIGVis VisPy, Viser, or Plotly using explicit nz_ny_nx or nx_ny_nz layout conversion. Use for orthogonal slices, masks, faults, RGT, horizons, bodies, wells, points, point clouds, splats, arbitrary lines, physical axes, static capture, or browser 3D.
---

# Volume 3D Plotting

## Purpose

Build a CIGVis 3D scene from forward-modeling volumes without reimplementing
slice, mesh, well, or point rendering. Make the domain layout and the CIGVis
`(x, y, z/time)` conversion explicit.

Read `../cigvis-api-plotting/SKILL.md` first. Read its
`references/axis-order.md` for every scene and `references/recipes.md` for the
selected VisPy, Viser, or Plotly engine.

## When to Use

- A 3D seismic, velocity, wavefield, error, or attribute volume must be viewed.
- Orthogonal or multiple slices need fault/RGT masks, horizons, bodies, wells,
  points, skins, arbitrary lines, point clouds, or splats.
- A desktop VisPy scene, browser Viser scene, or notebook Plotly scene is needed.

## Inputs

Required:

- `task_type: volume_3d`
- One 3D NumPy array or `.npy` path.
- `parameters.data_layout`: normally `nz_ny_nx`; use `nx_ny_nz` only when true.

Common parameters:

| Parameter | Meaning |
|---|---|
| `engine` | `vispy` (default), `viser`, or `plotly` |
| `slices` | Native-layout `[z, y, x]` for `nz_ny_nx`, or explicit `{x, y, z}` |
| `masks` | Fault/RGT/label volume specs with `data`/`path`, `cmap`, `alpha`, `excpt` |
| `surfaces` | Horizon specs using `create_surfaces` |
| `bodies` | Volume plus `level` specs using `create_bodies` |
| `well_logs` | Explicit CIGVis `(x, y, z[, value])` points |
| `line_logs` | One or more CIGVis line-log arrays |
| `points` | Picks or sparse interpreted points |
| `point_clouds` | Large point-cloud specs |
| `splats` / `gaussian_splats` | Surface/volume point rendering |
| `fault_skins` | Skin directory/path and `create_fault_skin` options |
| `arbitrary_lines` | Mapping with `path`/`anchor` and optional section `data`; the base volume is used otherwise |
| `display_range` | Half-open CIGVis data-coordinate ranges |
| `axis` / `view` | Public CIGVis axis and camera options |
| `save_path` | Static VisPy/Plotly output path |

All paths come from user configuration. Never use paths from CIGVis examples.

## Outputs

- `FigureResult.figure`: `Volume3DHandle` with CIGVis nodes, engine, and plot result.
- Optional `saved_paths` for an explicit static save.
- Metadata recording the input layout and selected engine.
- Clear dependency or API errors; no silent 3D fallback.

## Workflow

1. Inspect and require a declared layout when metadata is ambiguous.
2. Convert `nz_ny_nx -> nx_ny_nz` exactly once at the backend boundary.
3. Convert native slice indices to an explicit `{"x": ..., "y": ..., "z": ...}` map.
4. Call `create_slices`, then add each requested overlay with its dedicated
   public CIGVis `create_*` or `add_mask` API.
5. Add `create_axis` and `create_colorbar_from_nodes` by default.
6. Render with `plot3D` using engine-appropriate view/save options.
7. Verify shape, converted positions, labels, intervals, starts, and overlay alignment.

## Geophysical Conventions

- Framework default volume layout is `(nz, ny, nx)`.
- CIGVis 3D receives `(x, y, z/time)` after conversion.
- Axis labels and intervals follow `(x, y, z/time)`, not native array order.
- Depth/time is the CIGVis z axis and increases downward in the geological scene.
- Signed amplitude uses a symmetric `clim`; positive velocity/property volumes do not.
- A mask receives exactly the same volume transform as its base volume.
- A dense native horizon `(ny, nx)` becomes CIGVis `(nx, ny)`.

## Common Mistakes to Avoid

- Passing `(nz, ny, nx)` directly to `create_slices` and then labeling axis 0 as x.
- Treating `[z, y, x]` slice indices as CIGVis `[x, y, z]`.
- Transposing point coordinate columns without a declared point layout.
- Adding each mask in a list to one `add_mask` call; call it once per mask.
- Expecting Viser `save_path` to capture a browser scene automatically.
- Suppressing a missing VisPy/Viser/Plotly dependency and returning a misleading 2D plot.

## Default Behavior

- Use VisPy, center slices, gray/seismic rendering, a colorbar, and physical axis node.
- Use `nz_ny_nx` when the framework created the volume and no contrary metadata exists.
- Apply 99th-percentile symmetric clipping for signed wavefield/seismic amplitude.
- Leave explicit point/well coordinates in CIGVis `(x, y, z)` order.

## Verification

- For native shape `(nz, ny, nx)`, assert CIGVis receives `(nx, ny, nz)`.
- Assert converted slice positions reference the intended physical planes.
- Assert axis labels, starts, and intervals use x/y/z ordering.
- Assert every mask shape equals the converted base volume shape.
- Confirm the selected engine exposes every requested overlay API.

## Example Prompt

```text
Use $volume-3d-plotting for volume.npy declared as nz_ny_nx. Render with
CIGVis VisPy, slices at native [z=20, y=30, x=80], add fault.npy as a mask and
horizon.npy as a depth surface, add physical axes, and save volume.png.
```
