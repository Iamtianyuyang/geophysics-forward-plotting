# CIGVis API Recipes

## Contents

1. Repository adapter rule
2. 2D image and overlays
3. 1D trace and wiggle
4. VisPy 3D scene
5. Viser browser scene
6. SliceViewer

## Repository Adapter Rule

Inside `geophysics-forward-plotting`, use `cigvis_backend` so axis conversion,
fallback behavior, and dependency errors remain consistent. The direct CIGVis
recipes below explain what the adapter delegates to; do not duplicate adapter
logic in a skill.

## 2D Image and Overlays

```python
import cigvis

cigvis.set_order(False)  # data is already (depth/time, distance)
fg = {
    "img": cigvis.fg_image_args(fault, cmap="jet", alpha=0.45),
    "line": cigvis.line_args(horizon_x, horizon_z, color="yellow", lw=1.2),
    "marker": cigvis.marker_args(src_x, src_z, marker="*", c="red", s=60),
}
cigvis.plot2d(
    section,
    fg=fg,
    cmap="seismic",
    clim=[-clip, clip],
    xsample=[x0, dx],
    ysample=[t0, dt],
    xlabel="Receiver position (km)",
    ylabel="Time (s)",
    cbar="Amplitude",
    aspect="auto",
)
```

Preserve and restore the previous global order in reusable code. The repository
backend does this under a lock.

For subplots, pass `ax=axes[i]` and `show=False`. Suppress per-panel colorbars,
then create one colorbar from `axes[i].images[-1]` using the global `clim`.

## 1D Trace and Wiggle

```python
cigvis.plot1d(
    trace,
    dt=dt,
    beg=t0,
    orient="v",
    axis_label="Time (s)",
    value_label="Amplitude",
    fill_up=0.2,
)

cigvis.plot_multi_traces(
    gather[:, ::skip],
    dt=dt,
    beg=t0,       # beg is time/depth origin, not x origin
    inter=scale,  # 0 < scale <= 1
    fill_up=0.2,
    xlabel="Receiver position (km)",
    ylabel="Time (s)",
)
```

`plot_multi_traces` labels selected traces by ordinal index. The repository
backend replaces those labels with `x0 + original_trace_index * dx`.

## VisPy 3D Scene

```python
import cigvis

# volume_xyz is (x, y, z); position is explicit by axis name.
nodes = cigvis.create_slices(
    volume_xyz,
    pos={"x": [ix], "y": [iy], "z": [iz]},
    cmap="gray",
    clim=[-clip, clip],
    display_range={"z": (0, z_stop)},
)
nodes = cigvis.add_mask(nodes, fault_xyz, cmap="jet", alpha=0.45, excpt="min")
nodes += cigvis.create_surfaces(
    [horizon_xy], volume=volume_xyz, value_type="amp", cmap="seismic"
)
nodes += cigvis.create_bodies(body_xyz, level=0.5, color="cyan")
nodes += cigvis.create_well_logs(well_xyzv, logs_type="line")
nodes += cigvis.create_points(picks_xyz, color="yellow", size=3)
nodes += cigvis.create_axis(
    volume_xyz.shape,
    "axis",
    axis_pos="auto",
    intervals=[dx, dy, dz],
    starts=[x0, y0, z0],
    axis_labels=["Distance (km)", "Crossline (km)", "Depth (km)"],
)
nodes += cigvis.create_colorbar_from_nodes(nodes, "Amplitude", select="slices")
cigvis.plot3D(
    nodes,
    view=cigvis.Plot3DView(size=(900, 700)),
    save=cigvis.Plot3DSave(path="volume.png", transparent_bg=False),
)
```

Add point clouds, splats, fault skins, and arbitrary lines with their dedicated
`create_*` APIs. Do not convert explicit coordinate columns unless their input
layout is declared.

## Viser Browser Scene

```python
from cigvis import viserplot

nodes = viserplot.create_slices(volume_xyz, pos=[ix, iy, iz], cmap="gray")
nodes = viserplot.add_mask(nodes, fault_xyz, cmap="jet", alpha=0.45, excpt="min")
nodes += viserplot.create_surfaces([horizon_xy], value_type="depth")
nodes += viserplot.create_points(picks_xyz, color="yellow", r=4)
viserplot.plot3D(nodes, axis_scales=(1.0, 1.0, 1.7), fov=30.0)
```

For comparison, create one server per scene, call `link_servers`, render each
with `run_app=False`, then call `viserplot.run()`.

## SliceViewer

```python
from cigvis import sliceviewer as sv

# Native volume layout is (z, y, x), so display depth vertically and x horizontally.
nodes = sv.create_slice(
    volume_zyx,
    display_axes=(0, 2),
    indices={1: volume_zyx.shape[1] // 2},
    axis_labels=("Depth", "Crossline", "Distance"),
    cmap="gray",
    clim=[-clip, clip],
    interpolation="nearest",
    render_mode="float",
)
nodes = sv.add_mask(nodes, fault_zyx, cmap="jet", alpha=0.45, excpt="min")
nodes += sv.add_horizon(x, z, axes=(2, 0), color="yellow")
sv.show(nodes, port=5007, title="Wavefield slices", plot_height=520)
```

For 2-4 compatible volumes, build one node list per volume and pass the list of
node lists to `sv.show(..., grid=(rows, cols))`. Use identical display axes,
indices, colormap, and `clim`.
