# Geophysical Plotting Conventions

These conventions are enforced by `FigureReviewSkill` and documented in `core/conventions.py`.

## Axis Conventions

| Figure Type         | X Axis                      | Y Axis                    | Y Direction |
|---------------------|----------------------------|--------------------------|-------------|
| Velocity Model      | Distance (km)              | Depth (km)               | Downward ↓  |
| Shot Record         | Receiver position (km)     | Time (s)                 | Downward ↓  |
| Wavefield Snapshot  | Distance (km)              | Depth (km)               | Downward ↓  |
| Error Map           | Distance (km)              | Depth (km)               | Downward ↓  |
| Wiggle              | Distance (km)              | Time (s)                 | Downward ↓  |
| 3D Volume (slices)  | X/Inline (km)              | Depth (km)               | Downward ↓  |

**Rule:** Depth and time axes ALWAYS point downward in geophysical figures.

## Color and Colormap Conventions

| Data Type          | Colormap Type | Clim         | Recommended Colormaps     |
|--------------------|---------------|--------------|--------------------------|
| Velocity           | Sequential    | Asymmetric   | `jet`, `turbo`, `viridis` |
| Amplitude          | Diverging     | Symmetric    | `seismic`, `RdBu_r`, `gray` |
| Error (signed)     | Diverging     | Symmetric    | `seismic`, `bwr`, `RdBu_r`  |
| Error (absolute)   | Sequential    | Asymmetric   | `viridis`, `hot`, `afmhot`  |
| Error (relative)   | Diverging     | Symmetric    | `seismic`, `PuOr`           |

**Rule:** Symmetric clim `[-v, +v]` must be used for amplitude and signed error.

## Multi-Panel Comparison

- **All panels MUST use the same `vmin` / `vmax`** (global across all methods).
- **One shared colorbar** — never one per subplot.
- **Same extent** (physical coordinates) across all panels.
- **Same colormap** across all panels.

Violation of unified clim is the most common and most impactful error in comparison figures.

## Colorbar Labels (Mandatory)

| Figure Type        | Colorbar Label              |
|--------------------|-----------------------------|
| Velocity Model     | `Velocity (m/s)`            |
| Shot Record        | `Amplitude`                 |
| Wavefield Snapshot | `Amplitude`                 |
| Error (signed)     | `Signed Error`              |
| Error (absolute)   | `Absolute Error`            |
| Error (relative)   | `Relative Error`            |
| 3D Volume          | `Amplitude` or `Velocity`   |

**Rule:** Colorbar label is mandatory on all figures. Missing label = immediate review warning.

## Export Conventions

| Format | Resolution | Use Case                     |
|--------|-----------|------------------------------|
| PNG    | 600 dpi   | Default publication quality  |
| PDF    | Vector    | Journal submission (LaTeX)   |
| SVG    | Vector    | Web / slide figures          |

Minimum acceptable DPI: 300. Default: 600.

## Coordinate System

- Arrays are typically stored as `(nz, nx)` for 2D spatial data (depth × distance).
- Arrays are stored as `(nt, nx)` for shot records (time × trace).
- Arrays are stored as `(nz, ny, nx)` for 3D volumes.
- Always verify axis order before plotting to avoid transposed figures.

### CIGVis Order Mapping

- CIGVis defaults to `LINE_FIRST=True`; raw `cigvis.plot2d` therefore transposes
  input. The framework temporarily uses `LINE_FIRST=False` for normalized
  `(nt/nz, nx)` images and restores the previous global value.
- CIGVis 3D examples use `(x, y, z/time)`. Convert framework
  `(nz, ny, nx)` volumes with `transpose(2, 1, 0)` at the backend boundary.
- Convert native `(z, y, x)` slice indices to explicit CIGVis
  `{"x": [x], "y": [y], "z": [z]}` positions.
- Do not transpose SliceViewer volumes. Set `display_axes=(vertical, horizontal)`
  in native data-axis indices.
- Verify the rendered 2D image shape and actual y limits, not only labels.

## Physical Coordinates vs Array Indices

**Always use physical coordinates** (km, s) on axes, not array indices (0, 1, 2, ...).

Correct: `x = x0 + np.arange(nx) * dx`
Wrong: `x = np.arange(nx)`
