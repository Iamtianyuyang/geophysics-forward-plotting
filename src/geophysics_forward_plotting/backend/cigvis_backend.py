"""CIGVis 轻量封装层。

本模块将 FigureTask / DataContext 转换为 cigvis API 参数格式。
不复制 CIGVis 内部实现，只做接口适配。

CIGVis API 参考（examples/ 目录）:

  2D:  cigvis.plot2d(img, fg, cmap, clim, figsize, title, xlabel, ylabel,
                     cbar, aspect, xsample, ysample, xlabel_size, ylabel_size,
                     title_size, ticklabels_size, cbar_label_size, cbar_ticklabels_size,
                     save, dpi, show, ax)
  fg:  fg['img'] = cigvis.fg_image_args(data, cmap, alpha, clim, interpolation, show_cbar)
       fg['line'] = cigvis.line_args(x, y, color, lw, label)
       fg['marker'] = cigvis.marker_args(x, y, marker, c, s)
       fg['annotate'] = cigvis.annotate_args(x, y, labels)

  1D:  cigvis.plot1d(trace, dt, orient, axis_label, value_label, fill_up, fill_down,
                      fill_color, c, ax, show)
       cigvis.plot_multi_traces(traces, dt, beg, inter, c, fill_up, fill_down,
                                fill_color, xlabel, ylabel, lw, ax, show)

  3D:  nodes = cigvis.create_slices(volume, pos=[[x],[y],[z]], clim, cmap, interpolation)
       nodes = cigvis.add_mask(nodes, volume, cmap, alpha, clim, excpt='min')
       nodes += cigvis.create_colorbar_from_nodes(nodes, label, select='slices')
       cigvis.plot3D(nodes, view=Plot3DView(...), save=Plot3DSave(...))

  SV:  from cigvis import sliceviewer
       sv.create_slice(volume, display_axes, indices, axis_labels, cmap)

Gallery: https://cigvis.readthedocs.io/en/latest/gallery/index.html
Source:  https://github.com/JintaoLee-Roger/cigvis
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geophysics_forward_plotting.core.exceptions import BackendUnavailableError

if TYPE_CHECKING:
    from numpy.typing import NDArray

try:
    import cigvis  # type: ignore[import-untyped]

    _CIGVIS_AVAILABLE = True
except ImportError:
    _CIGVIS_AVAILABLE = False


def is_available() -> bool:
    return _CIGVIS_AVAILABLE


def _require_cigvis() -> None:
    if not _CIGVIS_AVAILABLE:
        raise BackendUnavailableError(
            "cigvis is not installed. Install it with: pip install cigvis\n"
            "See: https://github.com/JintaoLee-Roger/cigvis"
        )


# ---------------------------------------------------------------------------
# 2D — cigvis.plot2d()
# ---------------------------------------------------------------------------


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
    xsample: NDArray | None = None,
    ysample: NDArray | None = None,
) -> Any:
    """cigvis.plot2d() 显示 2D 图像切片。返回 matplotlib Figure。"""
    if _CIGVIS_AVAILABLE:
        return _cigvis_plot2d(
            data, extent=extent, cmap=cmap, clim=clim,
            x_label=x_label, y_label=y_label, title=title,
            colorbar_label=colorbar_label, figsize=figsize, dpi=dpi,
            xsample=xsample, ysample=ysample,
        )
    return _mpl_plot2d(
        data, extent=extent, cmap=cmap, clim=clim,
        x_label=x_label, y_label=y_label, title=title,
        colorbar_label=colorbar_label, figsize=figsize, dpi=dpi,
    )


def _cigvis_plot2d(
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
    xsample: NDArray | None,
    ysample: NDArray | None,
) -> Any:
    """
    cigvis.plot2d() — CIGVis 2D 绘图 API。

    cigvis.plot2d 不返回 fig，需提前创建 axes 传入 ax 参数。
    xsample/ysample 是 [start, step] 格式，不是完整数组。
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        from geophysics_forward_plotting.core.defaults import (
            LABEL_FONT_SIZE,
            TITLE_FONT_SIZE,
        )

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # xsample/ysample: CIGVis 期望 [start, step] 格式
        xs = [float(xsample[0]), float(np.diff(xsample[:2])[0])] if xsample is not None and len(xsample) >= 2 else None
        ys = [float(ysample[0]), float(np.diff(ysample[:2])[0])] if ysample is not None and len(ysample) >= 2 else None

        cigvis.plot2d(
            data,
            cmap=cmap,
            clim=list(clim) if clim else None,
            title=title or None,
            xlabel=x_label or None,
            ylabel=y_label or None,
            cbar=colorbar_label or None,
            aspect="auto",                   # 非正方形数据用 auto
            xsample=xs,
            ysample=ys,
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
        return fig
    except Exception:
        return _mpl_plot2d(
            data, extent=extent, cmap=cmap, clim=clim,
            x_label=x_label, y_label=y_label, title=title,
            colorbar_label=colorbar_label, figsize=figsize, dpi=dpi,
        )


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
) -> Any:
    """纯 matplotlib fallback。"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    vmin, vmax = (clim[0], clim[1]) if clim else (None, None)
    im = ax.imshow(
        data, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax,
        extent=extent, origin="upper",
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    cb = fig.colorbar(im, ax=ax)
    if colorbar_label:
        cb.set_label(colorbar_label)
    return fig


# ---------------------------------------------------------------------------
# 2D overlay — cigvis.fg_image_args / line_args / marker_args
# ---------------------------------------------------------------------------


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
) -> dict[str, Any] | None:
    """
    构建 CIGVis foreground overlay 字典。

    CIGVis fg 格式:
      fg = {}
      fg['img'] = [cigvis.fg_image_args(...)]       # 可叠加多个
      fg['line'] = [cigvis.line_args(...)]
      fg['marker'] = cigvis.marker_args(...)
      fg['annotate'] = cigvis.annotate_args(...)
    """
    if not _CIGVIS_AVAILABLE:
        return None

    fg: dict[str, Any] = {}

    if overlay_data is not None:
        fg["img"] = [
            cigvis.fg_image_args(
                overlay_data,
                cmap=overlay_cmap,
                alpha=overlay_alpha,
                clim=list(overlay_clim) if overlay_clim else None,
            )
        ]

    if line_x is not None and line_y is not None:
        fg["line"] = [
            cigvis.line_args(line_x, line_y, line_color, lw=line_lw, label=line_label)
        ]

    if marker_x is not None and marker_y is not None:
        fg["marker"] = cigvis.marker_args(
            marker_x, marker_y, marker=marker_style, c=marker_color, s=marker_size
        )

    return fg if fg else None


# ---------------------------------------------------------------------------
# 1D — cigvis.plot1d() / cigvis.plot_multi_traces()
# ---------------------------------------------------------------------------


def plot1d_wiggle(
    data: NDArray,
    *,
    dt: float = 0.002,
    x0: float = 0.0,
    skip: int = 1,
    gain: float = 1.0,
    fill_positive: bool = True,
    x_label: str = "Distance (km)",
    y_label: str = "Time (s)",
    title: str = "",
    figsize: tuple[float, float] = (7.0, 6.0),
    dpi: int = 600,
) -> Any:
    """
    cigvis.plot_multi_traces() 绘制多道 wiggle 图。

    CIGVis 示例 (examples/1D/2-plot_multi_traces.py):
      cigvis.plot_multi_traces(traces, dt=0.02, c='black', fill_up=0.2, ax=ax)
    """
    if _CIGVIS_AVAILABLE:
        return _cigvis_plot_multi_traces(
            data, dt=dt, x0=x0, skip=skip, gain=gain,
            fill_positive=fill_positive, x_label=x_label, y_label=y_label,
            title=title, figsize=figsize, dpi=dpi,
        )
    from geophysics_forward_plotting.backend.matplotlib_backend import wiggle_plot
    return wiggle_plot(
        data, dt=dt, dx=1.0, x0=x0, skip=skip, gain=gain,
        fill_positive=fill_positive, x_label=x_label, y_label=y_label,
        title=title, figsize=figsize, dpi=dpi,
    )


def _cigvis_plot_multi_traces(
    data: NDArray,
    *,
    dt: float,
    x0: float,
    skip: int,
    gain: float,
    fill_positive: bool,
    x_label: str,
    y_label: str,
    title: str,
    figsize: tuple[float, float],
    dpi: int,
) -> Any:
    """
    cigvis.plot_multi_traces()。

    fill_up 是 float 阈值（如 0.2），不是颜色字符串。
    fill_color='black' 设置填充颜色。
    traces 形状: (nt, n_traces) — 时间在第一轴。
    """
    try:
        import matplotlib.pyplot as plt

        sub = data[:, ::skip] if skip > 1 else data
        scaled = sub * gain

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        cigvis.plot_multi_traces(
            scaled,
            dt=dt,
            beg=x0,
            c="black",
            fill_up=0.2 if fill_positive else None,
            fill_color="black" if fill_positive else None,
            xlabel=x_label,
            ylabel=y_label,
            show=False,
            ax=ax,
        )
        if title:
            ax.set_title(title)
        return fig
    except Exception:
        from geophysics_forward_plotting.backend.matplotlib_backend import wiggle_plot
        return wiggle_plot(
            data, dt=dt, dx=1.0, x0=x0, skip=skip, gain=gain,
            fill_positive=fill_positive, x_label=x_label, y_label=y_label,
            title=title, figsize=figsize, dpi=dpi,
        )


# ---------------------------------------------------------------------------
# 3D — cigvis.create_slices() + cigvis.plot3D()
# ---------------------------------------------------------------------------


def plot3d_volume(
    data: NDArray,
    *,
    axis_labels: tuple[str, str, str] = ("X", "Y", "Z"),
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
    slices: tuple[int, int, int] | None = None,
    save_path: str | None = None,
) -> Any:
    """
    cigvis 3D API 渲染体数据。

    CIGVis 示例 (examples/3Dvispy/01-slice.py):
      nodes = cigvis.create_slices(volume, pos=[[x],[y],[z]], cmap='Petrel')
      nodes += cigvis.create_colorbar_from_nodes(nodes, 'Amplitude', select='slices')
      cigvis.plot3D(nodes, view=cigvis.Plot3DView(size=(800, 600)),
                    save=cigvis.Plot3DSave(path='output.png'))

    pos 格式: [[inline_indices], [crossline_indices], [time_indices]]
    """
    _require_cigvis()
    if data.ndim != 3:
        raise ValueError("plot3d_volume expects 3D array")

    ni, nj, nk = data.shape
    sx, sy, sz = slices or (ni // 2, nj // 2, nk // 2)

    nodes = cigvis.create_slices(
        data,
        pos=[[sx], [sy], [sz]],
        clim=list(clim) if clim else None,
        cmap=cmap,
    )
    nodes += cigvis.create_colorbar_from_nodes(
        nodes, "Amplitude", select="slices"
    )

    save_kw = cigvis.Plot3DSave(path=save_path, transparent_bg=False) if save_path else None
    cigvis.plot3D(
        nodes,
        view=cigvis.Plot3DView(size=(800, 600)),
        save=save_kw,
    )
    return nodes


# ---------------------------------------------------------------------------
# SliceViewer — cigvis.sliceviewer
# ---------------------------------------------------------------------------


def launch_sliceviewer(
    data: NDArray,
    *,
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
) -> Any:
    """
    cigvis SliceViewer 交互式切片浏览器。

    需要: pip install "cigvis[sliceviewer]"
    """
    _require_cigvis()
    try:
        from cigvis import sliceviewer  # type: ignore[import-untyped]
        viewer = sliceviewer.SliceViewer(data, cmap=cmap, clim=clim)
        viewer.show()
        return viewer
    except ImportError:
        raise BackendUnavailableError(
            "SliceViewer requires plotly and panel.\n"
            'Install: pip install "cigvis[sliceviewer]"'
        )
