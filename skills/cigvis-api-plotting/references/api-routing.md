# CIGVis Public API Routing

## Contents

1. 1D APIs
2. 2D APIs
3. 3D VisPy APIs
4. Viser browser APIs
5. Plotly/Jupyter APIs
6. SliceViewer APIs
7. Colormaps and I/O

This inventory is distilled from all code under the upstream CIGVis examples
tree. Prefer these public functions over internal node classes.

## 1D APIs

| API | Route |
|---|---|
| `cigvis.plot1d` | One trace, vertical or horizontal, optional positive/negative fill |
| `cigvis.plot_multi_traces` | Wiggle/wigb gather with trace fill and top trace axis |
| `cigvis.plot_signal_compare` | Station/component waveform comparisons |

## 2D APIs

| API | Route |
|---|---|
| `cigvis.plot2d` | Base seismic/model image, colorbar, physical sampled ticks, fonts, aspect |
| `cigvis.fg_image_args` | Fault, RGT, mask, or second image overlay |
| `cigvis.line_args` | Horizons, isolines, trajectories, comparison curves |
| `cigvis.marker_args` | Sources, receivers, wells, picks |
| `cigvis.annotate_args` | Labels attached to markers |

`plot2d` supports existing Matplotlib axes, so use it for CIGVis-rendered
subplots. Build one shared colorbar from the returned axes image for scientific
comparisons. It also supports discrete colorbars, custom tick labels, axis
sampling, font sizes, interpolation, and numeric aspect ratios.

## 3D VisPy APIs

| API | Route |
|---|---|
| `create_slices` | Orthogonal or multiple slices; `pos`, `display_range`, RGB/multi-source data |
| `add_mask` | RGT/fault/label overlays; call once per mask |
| `create_colorbar_from_nodes` / `create_colorbar` | Scene colorbars |
| `create_surfaces` | Dense/sparse horizons colored by depth, amplitude, or values |
| `create_bodies` | Isosurface geological bodies |
| `create_well_logs` / `create_line_logs` | Tube, line, point, or multi-curve well logs |
| `create_points` | Picks and sparse point markers |
| `create_point_cloud` | Large interpreted point clouds |
| `create_splats` | Point/surface/volume splats |
| `create_fault_skin` | Fault-skin meshes loaded from skin files |
| `create_arbitrary_line` | Folded or sampled arbitrary vertical sections |
| `create_axis` | Physical tick intervals, origins, labels, north pointer |
| `plot3D` | Canvas layout, shared camera, GUI, save, and rendering |

Use `Plot3DView`, `Plot3DSave`, and `Plot3DGui` configuration objects when the
installed CIGVis version provides them. Multiple node lists can be arranged in
a grid with shared cameras. Select the VisPy GUI backend before importing
CIGVis when an application requires a specific Qt backend.

## Viser Browser APIs

Import `from cigvis import viserplot` for browser-native 3D:

- `create_slices`, `add_mask`, `create_surfaces`, `create_bodies`
- `create_well_logs`, `create_points`
- `create_point_cloud`/`create_splats`
- `create_gaussian_splats`
- `create_server`, `link_servers`, `run`, `plot3D`

Use linked servers for synchronized method comparison. Browser point/splat
appearance depends on viewport, pixel ratio, camera, and screenshot region;
fix those values for reproducible captures.

## Plotly/Jupyter APIs

`cigvis.plotlyplot` mirrors the node-building model for notebook-oriented 3D
views. Use it only when the requested notebook workflow needs Plotly. Keep the
same line-first volume conversion used by other 3D backends.

## SliceViewer APIs

Import `from cigvis import sliceviewer as sv`:

| API | Route |
|---|---|
| `sv.create_slice` | Build a 2D/3D/4D dimension-aware slice node |
| `sv.add_mask` | Attach one same-shape overlay volume |
| `sv.add_horizon` | Horizon line annotation |
| `sv.add_fault` | Fault line annotation |
| `sv.add_well` | Well marker annotation |
| `sv.add_scatter` | Generic line/point annotation |
| `sv.link` | Link compatible viewer nodes |
| `sv.show` | Start one viewer or a comparison grid |
| `sv.build_layout` / `sv.create_server` | Advanced Panel integration |

Current examples do not construct `sliceviewer.SliceViewer`. Do not copy that
obsolete pattern.

## Colormaps and I/O

- Use CIGVis custom, stratum, discrete, and alpha-adjusted colormaps before
  inventing a new color pipeline.
- Use `cigvis.io.load_las` for LAS well logs and the documented skin/surface
  readers for their native formats.
- Keep data paths user-supplied. Never depend on upstream example data paths.
