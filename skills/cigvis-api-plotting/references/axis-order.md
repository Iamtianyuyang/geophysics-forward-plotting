# CIGVis Axis-Order Contract

## Contents

1. Framework layouts
2. CIGVis behavior
3. Conversion table
4. Direction checks
5. Overlay rules

## Framework Layouts

The executable framework uses semantic layouts, not shape heuristics:

| Layout | Axis 0 | Axis 1 | Axis 2 |
|---|---|---|---|
| `nt_nx` | time | distance/receiver | - |
| `nz_nx` | depth | distance | - |
| `nx_nt` | distance/receiver | time | - |
| `nx_nz` | distance | depth | - |
| `nz_ny_nx` | depth/time | y/crossline | x/distance |
| `nx_ny_nz` | x/distance | y/crossline | depth/time |

Declare `parameters.data_layout` in YAML when the layout is not already known.
Never infer physical meaning solely from which dimension is longest.

## CIGVis Behavior

CIGVis defaults to `LINE_FIRST=True` because its 3D examples use
`(inline, crossline, time)` or `(x, y, z)`.

- `cigvis.plot2d` transposes its input when `LINE_FIRST=True`.
- `cigvis.fg_image_args` applies the same transpose to foreground images.
- CIGVis 3D `create_slices` examples use `(x, y, z/time)`.
- SliceViewer is dimension-generic. `display_axes` is `(y_axis, x_axis)` in
  native data-axis indices and does not require a volume transpose.

Use the repository backend. It temporarily sets `LINE_FIRST=False` around 2D
calls and restores the previous value. It converts 3D arrays before calling
CIGVis and temporarily uses `LINE_FIRST=True` for those calls.

## Conversion Table

| Input | CIGVis operation | Output/order |
|---|---|---|
| `(nt, nx)` | 2D backend | unchanged `(nt, nx)` |
| `(nz, nx)` | 2D backend | unchanged `(nz, nx)` |
| `(nx, nt)` | 2D normalization | transpose to `(nt, nx)` |
| `(nx, nz)` | 2D normalization | transpose to `(nz, nx)` |
| `(nz, ny, nx)` | 3D adapter | transpose `(2, 1, 0)` to `(nx, ny, nz)` |
| `(nx, ny, nz)` | 3D adapter | unchanged |
| horizon `(ny, nx)` | surface adapter | transpose to `(nx, ny)` |

For native `(nz, ny, nx)` slice indices `(z, y, x)`, convert to:

```python
{"x": [x], "y": [y], "z": [z]}
```

Prefer this dictionary form over a positional list because it makes axis
ownership explicit.

## Direction Checks

For Matplotlib-backed CIGVis 2D figures:

```python
image = fig.axes[0].images[0]
assert image.get_array().shape == input_vertical_first.shape
assert fig.axes[0].get_ylim()[0] > fig.axes[0].get_ylim()[1]
```

Check tick values against sampling:

```text
x(i) = x0 + i * dx
z(k) = z0 + k * dz
t(k) = t0 + k * dt
```

Axis labels describe physical meaning, not array-axis numbers.

## Overlay Rules

- Transform a 3D mask with the same layout conversion as the base volume.
- Transform a dense horizon `(ny, nx)` to `(nx, ny)` for CIGVis surfaces.
- Point, well, skin, and arbitrary-line coordinates must already be explicit
  CIGVis `(x, y, z)` coordinates. Do not transpose coordinate columns unless a
  declared point layout requires it.
- Base volume and mask shapes must match after conversion.
- SliceViewer masks remain in the same native layout and shape as its volume.
