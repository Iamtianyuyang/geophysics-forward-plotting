---
name: sliceviewer-plotting
description: Build current CIGVis SliceViewer workflows with create_slice, add_mask, annotations, and show for one or more 2D/3D/4D arrays. Use for browser-based inline/crossline/depth or time browsing, remote-server exploration, overlay quality control, and synchronized comparison grids.
---

# SliceViewer Plotting

## Purpose

Explore one or more forward-modeling volumes through CIGVis's current
Panel/Plotly SliceViewer API. Preserve native array order and declare which two
data axes are displayed vertically and horizontally.

Read `../cigvis-api-plotting/SKILL.md`, especially
`references/axis-order.md`, before choosing `display_axes`.

## When to Use

- A remote or local browser should browse slices without a heavy 3D scene.
- Inline, crossline, depth, time, model, and wavefield volumes need QC.
- Two to four compatible volumes need a synchronized comparison grid.
- Fault masks, horizons, wells, or generic annotations should track a slice.

## Inputs

- `task_type: sliceviewer`
- One or more same-grid 3D NumPy arrays or `.npy` paths.
- `parameters.data_layout`, normally `nz_ny_nx`.
- `display_axes=(vertical_axis, horizontal_axis)` in native array-axis indices.
- Hidden-axis `indices`, axis labels, colormap, shared `clim`, and interpolation.
- Optional `masks`, `annotations`, `grid`, `port`, and `show_options`.

For native `(nz, ny, nx)`, use `display_axes=(0, 2)` to show depth vertically
and x horizontally while selecting a y index.

## Outputs

- `FigureResult.figure`: `SliceViewerHandle` containing node groups and optional server.
- One node group for one volume or a list of groups for comparison.
- Metadata recording native layout and display axes.
- An actionable error when `cigvis[sliceviewer]` dependencies are missing.

## Workflow

1. Confirm every array layout and grid compatibility.
2. Keep arrays in native layout; do not apply the 3D VisPy `(x, y, z)` transpose.
3. Call `sv.create_slice` with explicit `display_axes`, hidden indices, and labels.
4. Add same-shape masks with `sv.add_mask`.
5. Add annotations with `sv.add_horizon`, `add_fault`, `add_well`, or `add_scatter`.
6. For comparisons, build one node group per volume with identical display
   options and call `sv.show(groups, grid=(rows, cols))`.
7. Verify the extracted frame shape and axis labels before presenting the viewer.

## Geophysical Conventions

- `display_axes` is `(y_axis, x_axis)`, not `(x_axis, y_axis)`.
- For `nz_ny_nx`, depth/time axis 0 is vertical and distance axis 2 is horizontal.
- Use identical indices, colormap, `clim`, and grid metadata for comparisons.
- Signed wavefields use a shared symmetric `clim`.
- Masks must have the exact native shape of their base volume.
- Axis labels include physical meaning and units even though controls use indices.

## Common Mistakes to Avoid

- Calling obsolete `sliceviewer.SliceViewer(volume).show()` code.
- Applying the VisPy 3D transpose before `sv.create_slice`.
- Reversing `display_axes` and obtaining a transposed frame.
- Including a displayed axis in hidden `indices`.
- Comparing independently normalized volumes.
- Starting a Panel server in CI; use `show: false` to build and test nodes only.

## Default Behavior

- Use current `create_slice`/`add_mask`/`show` APIs.
- For `nz_ny_nx`, default to `display_axes=(0, 2)` and select center y.
- Use `render_mode="float"`, nearest interpolation, and auto aspect.
- Start the viewer unless `parameters.show` is false.
- Raise a clear dependency error; never silently replace SliceViewer with a static plot.

## Verification

- Assert the SliceNode frame shape matches the selected native axes in the
  declared `(vertical, horizontal)` order.
- Assert masks match the base volume shape.
- Assert comparison groups share `clim`, display axes, and fixed indices.
- Assert `show: false` does not start a server.

## Example Prompt

```text
Use $sliceviewer-plotting to compare three nz_ny_nx wavefield volumes. Show
depth versus distance at the center y index, use one symmetric clim, overlay
fault.npy, arrange a 2x2 grid, and run on port 5007.
```
