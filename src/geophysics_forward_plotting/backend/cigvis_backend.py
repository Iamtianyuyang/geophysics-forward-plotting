"""Thin, version-tolerant adapters around public CIGVis APIs.

The normalized 2D contract is ``(vertical, horizontal)`` and the normalized
3D contract is explicit through ``DataLayout``. CIGVis itself uses line-first
``(x, y, z/time)`` volumes, so conversion happens at this boundary only.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, Any

import numpy as np

from geophysics_forward_plotting.backend.adapters import (
    normalize_data_layout,
    to_cigvis_position,
    to_cigvis_surface,
    to_cigvis_volume,
)
from geophysics_forward_plotting.core.enums import DataLayout
from geophysics_forward_plotting.core.exceptions import (
    BackendRenderError,
    BackendUnavailableError,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

try:
    import cigvis as _cigvis  # type: ignore[import-untyped]
except ImportError:
    _cigvis = None

cigvis: Any | None = _cigvis
_CIGVIS_AVAILABLE = cigvis is not None
_CONFIG_LOCK = RLock()


@dataclass(slots=True)
class Volume3DHandle:
    """Nodes plus the selected interactive CIGVis engine."""

    nodes: list[Any]
    engine: str
    plot_result: Any = None


@dataclass(slots=True)
class SliceViewerHandle:
    """SliceViewer nodes and an optional running Panel server."""

    nodes: Any
    server: Any = None


def is_available() -> bool:
    return _CIGVIS_AVAILABLE


def _require_cigvis(feature: str = "CIGVis rendering") -> Any:
    if not _CIGVIS_AVAILABLE or cigvis is None:
        raise BackendUnavailableError(
            f"{feature} requires cigvis. Install it with: pip install cigvis\n"
            "See: https://github.com/JintaoLee-Roger/cigvis"
        )
    return cigvis


@contextmanager
def _data_order(line_first: bool) -> Iterator[None]:
    """Temporarily set CIGVis's global order and always restore it."""
    module = _require_cigvis()
    if not hasattr(module, "is_line_first") or not hasattr(module, "set_order"):
        yield
        return

    with _CONFIG_LOCK:
        previous = bool(module.is_line_first())
        module.set_order(line_first)
        try:
            yield
        finally:
            module.set_order(previous)


def _finite_clim(data: NDArray, clim: tuple[float, float] | None) -> list[float]:
    if clim is not None:
        return [float(clim[0]), float(clim[1])]
    finite = np.asarray(data)[np.isfinite(data)]
    if finite.size == 0:
        return [0.0, 1.0]
    vmin, vmax = float(finite.min()), float(finite.max())
    if vmin == vmax:
        pad = abs(vmin) * 0.01 or 1.0
        return [vmin - pad, vmax + pad]
    return [vmin, vmax]


def _sample_pair(samples: NDArray | Sequence[float] | None) -> list[float] | None:
    if samples is None or len(samples) < 2:
        return None
    return [float(samples[0]), float(samples[1] - samples[0])]


def _set_y_direction(ax: Any, *, downward: bool) -> None:
    bottom, top = ax.get_ylim()
    is_downward = bottom > top
    if downward != is_downward:
        ax.invert_yaxis()


def plot2d_image(
    data: NDArray,
    *,
    extent: tuple[float, float, float, float] | None = None,
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
    x_label: str = "",
    y_label: str = "",
    title: str = "",
    colorbar_label: str = "",
    figsize: tuple[float, float] = (7.0, 4.5),
    dpi: int = 600,
    xsample: NDArray | Sequence[float] | None = None,
    ysample: NDArray | Sequence[float] | None = None,
    fg: Mapping[str, Any] | None = None,
    interpolation: str = "bicubic",
    aspect: str | float = "auto",
    discrete: bool = False,
    tick_labels: Sequence[str] | None = None,
    show_legend: bool = False,
    downward: bool = True,
    ax: Any = None,
    show_colorbar: bool = True,
) -> Any:
    """Render a vertical-first 2D geophysical image."""
    if _CIGVIS_AVAILABLE:
        return _cigvis_plot2d(
            data,
            cmap=cmap,
            clim=clim,
            x_label=x_label,
            y_label=y_label,
            title=title,
            colorbar_label=colorbar_label,
            figsize=figsize,
            dpi=dpi,
            xsample=xsample,
            ysample=ysample,
            fg=fg,
            interpolation=interpolation,
            aspect=aspect,
            discrete=discrete,
            tick_labels=tick_labels,
            show_legend=show_legend,
            downward=downward,
            ax=ax,
            show_colorbar=show_colorbar,
        )
    return _mpl_plot2d(
        data,
        extent=extent,
        cmap=cmap,
        clim=clim,
        x_label=x_label,
        y_label=y_label,
        title=title,
        colorbar_label=colorbar_label,
        figsize=figsize,
        dpi=dpi,
        downward=downward,
        ax=ax,
        show_colorbar=show_colorbar,
    )


def _cigvis_plot2d(
    data: NDArray,
    *,
    cmap: str,
    clim: tuple[float, float] | None,
    x_label: str,
    y_label: str,
    title: str,
    colorbar_label: str,
    figsize: tuple[float, float],
    dpi: int,
    xsample: NDArray | Sequence[float] | None,
    ysample: NDArray | Sequence[float] | None,
    fg: Mapping[str, Any] | None,
    interpolation: str,
    aspect: str | float,
    discrete: bool,
    tick_labels: Sequence[str] | None,
    show_legend: bool,
    downward: bool,
    ax: Any,
    show_colorbar: bool,
) -> Any:
    import matplotlib.pyplot as plt

    from geophysics_forward_plotting.core.defaults import LABEL_FONT_SIZE, TITLE_FONT_SIZE

    module = _require_cigvis("2D plotting")
    if data.ndim != 2:
        raise BackendRenderError(f"cigvis.plot2d expects 2D data, got shape={data.shape}")

    created_axes = ax is None
    if created_axes:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.figure

    try:
        # CIGVis transposes plot2d input when line_first=True. The framework
        # contract is already vertical-first, so disable that transpose here.
        with _data_order(False):
            module.plot2d(
                data,
                fg=dict(fg) if fg else None,
                cmap=cmap,
                clim=_finite_clim(data, clim),
                interpolation=interpolation,
                title=title or None,
                xlabel=x_label or None,
                ylabel=y_label or None,
                cbar=(colorbar_label or "") if show_colorbar else None,
                discrete=discrete,
                tick_labels=list(tick_labels) if tick_labels else None,
                show_legend=show_legend,
                aspect=aspect,
                xsample=_sample_pair(xsample),
                ysample=_sample_pair(ysample),
                xlabel_size=LABEL_FONT_SIZE,
                ylabel_size=LABEL_FONT_SIZE,
                title_size=TITLE_FONT_SIZE,
                cbar_label_size=LABEL_FONT_SIZE,
                ticklabels_size=10,
                cbar_ticklabels_size=10,
                dpi=dpi,
                show=False,
                ax=ax,
            )
    except Exception as exc:
        if created_axes:
            plt.close(fig)
        raise BackendRenderError(f"cigvis.plot2d failed: {exc}") from exc

    _set_y_direction(ax, downward=downward)
    return fig


def _mpl_plot2d(
    data: NDArray,
    *,
    extent: tuple[float, float, float, float] | None,
    cmap: str,
    clim: tuple[float, float] | None,
    x_label: str,
    y_label: str,
    title: str,
    colorbar_label: str,
    figsize: tuple[float, float],
    dpi: int,
    downward: bool,
    ax: Any,
    show_colorbar: bool,
) -> Any:
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.figure
    vmin, vmax = (clim[0], clim[1]) if clim else (None, None)
    im = ax.imshow(
        data,
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        origin="upper",
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    _set_y_direction(ax, downward=downward)
    if show_colorbar:
        cb = fig.colorbar(im, ax=ax)
        if colorbar_label:
            cb.set_label(colorbar_label)
    return fig


def plot2d_on_axes(data: NDArray, *, ax: Any, **kwargs: Any) -> Any:
    """Use CIGVis plot2d on an existing axes and return its image artist."""
    kwargs.pop("colorbar_label", None)
    plot2d_image(
        data,
        ax=ax,
        colorbar_label="",
        show_colorbar=False,
        **kwargs,
    )
    if not ax.images:
        raise BackendRenderError("2D backend did not create an image artist")
    return ax.images[-1]


def make_fg_overlay(
    overlay_data: NDArray | None = None,
    overlay_cmap: str = "jet",
    overlay_alpha: float = 0.5,
    overlay_clim: tuple[float, float] | None = None,
    line_x: NDArray | None = None,
    line_y: NDArray | None = None,
    line_color: str = "white",
    line_lw: float = 1.0,
    line_label: str | None = None,
    marker_x: NDArray | None = None,
    marker_y: NDArray | None = None,
    marker_style: str = "^",
    marker_color: str = "red",
    marker_size: float = 40,
    annotation_text: Sequence[str] | None = None,
) -> dict[str, Any] | None:
    """Build a CIGVis foreground dictionary without nesting helper results."""
    if not _CIGVIS_AVAILABLE:
        return None
    module = _require_cigvis("2D overlays")
    fg: dict[str, Any] = {}

    if overlay_data is not None:
        with _data_order(False):
            fg["img"] = module.fg_image_args(
                overlay_data,
                cmap=overlay_cmap,
                alpha=overlay_alpha,
                clim=list(overlay_clim) if overlay_clim else None,
            )
    if line_x is not None and line_y is not None:
        fg["line"] = module.line_args(
            line_x,
            line_y,
            line_color,
            lw=line_lw,
            label=line_label,
        )
    if marker_x is not None and marker_y is not None:
        fg["marker"] = module.marker_args(
            marker_x,
            marker_y,
            marker=marker_style,
            c=marker_color,
            s=marker_size,
        )
        if annotation_text:
            fg["annotate"] = module.annotate_args(
                marker_x,
                marker_y,
                list(annotation_text),
            )
    return fg or None


def plot1d_trace(
    data: NDArray,
    *,
    dt: float = 0.002,
    t0: float = 0.0,
    axis_label: str = "Time (s)",
    value_label: str = "Amplitude",
    title: str = "",
    fill_positive: bool = False,
    figsize: tuple[float, float] = (3.5, 6.0),
    dpi: int = 600,
) -> Any:
    """Render one vertical trace with cigvis.plot1d."""
    module = _require_cigvis("1D trace plotting")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    module.plot1d(
        data,
        dt=dt,
        beg=t0,
        orient="v",
        title=title or None,
        axis_label=axis_label,
        value_label=value_label,
        fill_up=0.2 if fill_positive else None,
        fill_color="black" if fill_positive else None,
        c="black",
        show=False,
        ax=ax,
    )
    _set_y_direction(ax, downward=True)
    return fig


def plot1d_wiggle(
    data: NDArray,
    *,
    dt: float = 0.002,
    dx: float = 1.0,
    x0: float = 0.0,
    t0: float = 0.0,
    skip: int = 1,
    gain: float = 1.0,
    scale: float = 1.0,
    fill_positive: bool = True,
    x_label: str = "Distance (km)",
    y_label: str = "Time (s)",
    title: str = "",
    figsize: tuple[float, float] = (7.0, 6.0),
    dpi: int = 600,
) -> Any:
    """Prefer cigvis.plot_multi_traces and preserve physical trace positions."""
    if _CIGVIS_AVAILABLE:
        return _cigvis_plot_multi_traces(
            data,
            dt=dt,
            dx=dx,
            x0=x0,
            t0=t0,
            skip=skip,
            gain=gain,
            scale=scale,
            fill_positive=fill_positive,
            x_label=x_label,
            y_label=y_label,
            title=title,
            figsize=figsize,
            dpi=dpi,
        )
    from geophysics_forward_plotting.backend.matplotlib_backend import wiggle_plot

    return wiggle_plot(
        data,
        dt=dt,
        dx=dx,
        x0=x0,
        t0=t0,
        skip=skip,
        gain=gain * scale,
        fill_positive=fill_positive,
        x_label=x_label,
        y_label=y_label,
        title=title,
        figsize=figsize,
        dpi=dpi,
    )


def _cigvis_plot_multi_traces(
    data: NDArray,
    *,
    dt: float,
    dx: float,
    x0: float,
    t0: float,
    skip: int,
    gain: float,
    scale: float,
    fill_positive: bool,
    x_label: str,
    y_label: str,
    title: str,
    figsize: tuple[float, float],
    dpi: int,
) -> Any:
    import matplotlib.pyplot as plt

    module = _require_cigvis("wiggle plotting")
    if data.ndim != 2:
        raise BackendRenderError(f"Wiggle plotting expects (nt, nx), got {data.shape}")
    if skip < 1:
        raise BackendRenderError("skip must be at least 1")
    if not 0 < scale <= 1:
        raise BackendRenderError("CIGVis wiggle scale/inter must be in (0, 1]")

    source_indices = np.arange(0, data.shape[1], skip)
    traces = data[:, source_indices] * gain
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    try:
        module.plot_multi_traces(
            traces,
            dt=dt,
            beg=t0,
            inter=scale,
            c="black",
            fill_up=0.2 if fill_positive else None,
            fill_color="black" if fill_positive else None,
            xlabel=x_label,
            ylabel=y_label,
            show=False,
            ax=ax,
        )
    except Exception as exc:
        plt.close(fig)
        raise BackendRenderError(f"cigvis.plot_multi_traces failed: {exc}") from exc

    labels: list[str] = []
    for label in ax.get_xticklabels():
        try:
            displayed_index = int(float(label.get_text()))
            original_index = source_indices[displayed_index]
            labels.append(f"{x0 + original_index * dx:g}")
        except (ValueError, IndexError):
            labels.append(label.get_text())
    ax.set_xticks(ax.get_xticks(), labels)
    if title:
        ax.set_title(title)
    _set_y_direction(ax, downward=True)
    return fig


def _resolve_3d_api(engine: str) -> Any:
    module = _require_cigvis("3D volume rendering")
    normalized = engine.lower()
    if normalized == "vispy":
        api = module
    elif normalized in {"viser", "browser"}:
        api = module.viserplot
    elif normalized in {"plotly", "jupyter"}:
        api = module.plotlyplot
    else:
        raise BackendRenderError("3D engine must be 'vispy', 'viser', or 'plotly'")
    try:
        create_slices = api.create_slices
        plot3d = api.plot3D
    except (AttributeError, ImportError) as exc:
        raise BackendUnavailableError(
            f"CIGVis {normalized} backend is unavailable. Install cigvis[{normalized}]."
        ) from exc
    if not callable(create_slices) or not callable(plot3d):
        raise BackendUnavailableError(f"CIGVis {normalized} backend is incomplete")
    return api


def _overlay_specs(overlays: Mapping[str, Sequence[Any]] | None, key: str) -> Sequence[Any]:
    return () if overlays is None else overlays.get(key, ())


def _split_spec(spec: Any) -> tuple[Any, dict[str, Any]]:
    if isinstance(spec, Mapping):
        kwargs = dict(spec)
        if "data" not in kwargs:
            raise BackendRenderError("A 3D overlay mapping must contain a 'data' array")
        return kwargs.pop("data"), kwargs
    return spec, {}


def _add_3d_overlays(
    api: Any,
    nodes: list[Any],
    base_volume: NDArray,
    overlays: Mapping[str, Sequence[Any]] | None,
    layout: DataLayout,
) -> list[Any]:
    for spec in _overlay_specs(overlays, "masks"):
        data, kwargs = _split_spec(spec)
        nodes = api.add_mask(nodes, to_cigvis_volume(np.asarray(data), layout), **kwargs)

    for spec in _overlay_specs(overlays, "surfaces"):
        data, kwargs = _split_spec(spec)
        surface = to_cigvis_surface(np.asarray(data), layout)
        if kwargs.get("value_type") == "amp":
            kwargs.setdefault("volume", base_volume)
        nodes.extend(api.create_surfaces([surface], **kwargs))

    for spec in _overlay_specs(overlays, "bodies"):
        data, kwargs = _split_spec(spec)
        nodes.extend(api.create_bodies(to_cigvis_volume(np.asarray(data), layout), **kwargs))

    arbitrary_lines = _overlay_specs(overlays, "arbitrary_lines")
    if arbitrary_lines and not hasattr(api, "create_arbitrary_line"):
        raise BackendRenderError(
            "CIGVis engine does not provide create_arbitrary_line required by overlays"
        )
    for spec in arbitrary_lines:
        if not isinstance(spec, Mapping):
            raise BackendRenderError("An arbitrary-line overlay must be a mapping")
        kwargs = dict(spec)
        if "data" not in kwargs and "volume" not in kwargs:
            kwargs["volume"] = base_volume
        kwargs.setdefault("nodes", nodes)
        nodes.extend(api.create_arbitrary_line(**kwargs))

    direct_creators = {
        "well_logs": "create_well_logs",
        "line_logs": "create_line_logs",
        "points": "create_points",
        "point_clouds": "create_point_cloud",
        "splats": "create_splats",
        "gaussian_splats": "create_gaussian_splats",
        "fault_skins": "create_fault_skin",
    }
    for key, creator_name in direct_creators.items():
        specs = _overlay_specs(overlays, key)
        if specs and not hasattr(api, creator_name):
            raise BackendRenderError(
                f"CIGVis engine does not provide {creator_name} required by overlay '{key}'"
            )
        for spec in specs:
            data, kwargs = _split_spec(spec)
            nodes.extend(getattr(api, creator_name)(data, **kwargs))
    return nodes


def plot3d_volume(
    data: NDArray,
    *,
    layout: DataLayout | str | None = DataLayout.NZ_NY_NX,
    engine: str = "vispy",
    axis_labels: tuple[str, str, str] = ("Distance (km)", "Y (km)", "Depth (km)"),
    intervals: tuple[float, float, float] = (1.0, 1.0, 1.0),
    starts: tuple[float, float, float] = (0.0, 0.0, 0.0),
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
    slices: tuple[int, int, int] | list[int] | dict[str, Any] | None = None,
    overlays: Mapping[str, Sequence[Any]] | None = None,
    colorbar_label: str = "Amplitude",
    display_range: Mapping[str, tuple[int, int]] | None = None,
    interpolation: str = "cubic",
    add_axis: bool = True,
    axis_kwargs: Mapping[str, Any] | None = None,
    view_kwargs: Mapping[str, Any] | None = None,
    save_path: str | Path | None = None,
) -> Volume3DHandle:
    """Create CIGVis 3D nodes using VisPy, Viser, or Plotly."""
    resolved_layout = normalize_data_layout(layout, ndim=3)
    volume = to_cigvis_volume(data, resolved_layout)
    position = to_cigvis_position(slices, shape=data.shape, layout=resolved_layout)
    api = _resolve_3d_api(engine)

    try:
        with _data_order(True):
            nodes = api.create_slices(
                volume,
                pos=position,
                clim=list(clim) if clim else None,
                cmap=cmap,
                interpolation=interpolation,
                display_range=dict(display_range) if display_range else None,
            )
            nodes = _add_3d_overlays(api, nodes, volume, overlays, resolved_layout)

            if colorbar_label and hasattr(api, "create_colorbar_from_nodes"):
                nodes.extend(
                    api.create_colorbar_from_nodes(nodes, colorbar_label, select="slices")
                )
            if add_axis and hasattr(api, "create_axis"):
                kwargs = dict(axis_kwargs or {})
                kwargs.setdefault("axis_pos", "auto")
                kwargs.setdefault("axis_labels", list(axis_labels))
                kwargs.setdefault("intervals", list(intervals))
                kwargs.setdefault("starts", list(starts))
                nodes.extend(api.create_axis(volume.shape, "axis", **kwargs))

            plot_result = _plot_3d_nodes(
                api,
                nodes,
                engine=engine,
                view_kwargs=view_kwargs,
                save_path=save_path,
            )
    except (BackendRenderError, BackendUnavailableError):
        raise
    except Exception as exc:
        raise BackendRenderError(f"CIGVis 3D rendering failed: {exc}") from exc
    return Volume3DHandle(nodes=list(nodes), engine=engine, plot_result=plot_result)


def _plot_3d_nodes(
    api: Any,
    nodes: list[Any],
    *,
    engine: str,
    view_kwargs: Mapping[str, Any] | None,
    save_path: str | Path | None,
) -> Any:
    view = dict(view_kwargs or {})
    normalized = engine.lower()
    if normalized in {"viser", "browser"}:
        if save_path is not None:
            raise BackendRenderError("Viser screenshots are captured in the browser, not save_path")
        return api.plot3D(nodes, **view)

    module = _require_cigvis("3D plotting")
    view.setdefault("size", (800, 600))
    view_option = module.Plot3DView(**view) if hasattr(module, "Plot3DView") else view
    save_option = None
    if save_path is not None:
        save_kwargs = {"path": str(save_path), "transparent_bg": False}
        save_option = (
            module.Plot3DSave(**save_kwargs)
            if hasattr(module, "Plot3DSave")
            else save_kwargs
        )
    return api.plot3D(nodes, view=view_option, save=save_option)


def launch_sliceviewer(
    data: NDArray,
    *,
    comparison_data: Sequence[NDArray] = (),
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
    display_axes: tuple[int, int] = (0, 2),
    indices: Mapping[int, int] | Sequence[int] | None = None,
    axis_labels: Sequence[str] = ("Depth", "Crossline", "Distance"),
    aspect: str | float = "auto",
    interpolation: str = "nearest",
    render_mode: str = "float",
    masks: Sequence[Mapping[str, Any]] = (),
    annotations: Sequence[Mapping[str, Any]] = (),
    grid: tuple[int, int] | None = None,
    show: bool = True,
    show_kwargs: Mapping[str, Any] | None = None,
) -> SliceViewerHandle:
    """Build the current CIGVis create_slice/add_mask/show viewer workflow."""
    module = _require_cigvis("SliceViewer")
    try:
        sv = module.sliceviewer
        create_slice = sv.create_slice
    except (AttributeError, ImportError) as exc:
        raise BackendUnavailableError(
            'SliceViewer requires: pip install "cigvis[sliceviewer]"'
        ) from exc

    arrays = (data, *comparison_data)
    groups: list[list[Any]] = []
    for volume in arrays:
        nodes = create_slice(
            volume,
            display_axes=display_axes,
            indices=indices,
            axis_labels=tuple(axis_labels),
            cmap=cmap,
            clim=list(clim) if clim else None,
            aspect=aspect,
            interpolation=interpolation,
            render_mode=render_mode,
        )
        for mask in masks:
            spec = dict(mask)
            mask_data = spec.pop("data")
            nodes = sv.add_mask(nodes, mask_data, **spec)
        for annotation in annotations:
            spec = dict(annotation)
            kind = str(spec.pop("kind"))
            creator = getattr(sv, f"add_{kind}", None)
            if creator is None:
                raise BackendRenderError(f"Unknown SliceViewer annotation kind: {kind}")
            nodes.extend(creator(**spec))
        groups.append(nodes)

    viewer_nodes: Any = groups[0] if len(groups) == 1 else groups
    server = None
    if show:
        kwargs = dict(show_kwargs or {})
        if len(groups) > 1 and grid is not None:
            kwargs["grid"] = grid
        server = sv.show(viewer_nodes, **kwargs)
    return SliceViewerHandle(nodes=viewer_nodes, server=server)
