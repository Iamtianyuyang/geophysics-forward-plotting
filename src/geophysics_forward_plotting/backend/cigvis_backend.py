"""CIGVis 轻量封装层。

本模块不复制 CIGVis 内部实现，只做接口适配，将本框架的
FigureTask / DataContext 转换为 cigvis 所需的参数格式。

CIGVis API（参考 examples/ 目录）：

  2D:
    cigvis.plot2d(img, cmap, clim, figsize, title, xlabel, ylabel,
                  cbar, aspect, xsample, ysample, xlabel_size, ylabel_size,
                  title_size, ticklabels_size, cbar_label_size, cbar_ticklabels_size,
                  save, dpi, show, ax)

  1D:
    cigvis.plot1d(data, dt, beg, orient, figsize, title, axis_label,
                  value_label, fill_up, fill_down, fill_color, c,
                  save, show, dpi, ax)
    cigvis.plot_multi_traces(data, dt, beg, inter, c, fill_up, fill_down,
                             fill_color, figsize, xlabel, ylabel, save,
                             show, dpi, lw, ax)

  3D:
    nodes = cigvis.create_slices(volume, pos, clim, cmap)
    nodes += cigvis.create_colorbar_from_nodes(nodes, label, select='slices')
    cigvis.plot3D(nodes, view=cigvis.Plot3DView(...), save=cigvis.Plot3DSave(...))

  SliceViewer:
    pip install "cigvis[sliceviewer]"

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
# 2D 接口适配 — cigvis.plot2d()
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
    """
    使用 cigvis.plot2d() 显示 2D 图像切片。

    cigvis.plot2d 不返回 fig，需提前创建 axes 传入 ax 参数。
    """
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
    """调用 cigvis.plot2d() — CIGVis 官方 2D 绘图 API。"""
    try:
        import matplotlib.pyplot as plt

        from geophysics_forward_plotting.core.defaults import (
            LABEL_FONT_SIZE,
            TITLE_FONT_SIZE,
        )

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        cigvis.plot2d(
            data,
            cmap=cmap,
            clim=list(clim) if clim else None,
            title=title or None,
            xlabel=x_label or None,
            ylabel=y_label or None,
            cbar=colorbar_label or None,       # cbar 是色条标签字符串
            xlabel_size=LABEL_FONT_SIZE,
            ylabel_size=LABEL_FONT_SIZE,
            title_size=TITLE_FONT_SIZE,
            cbar_label_size=LABEL_FONT_SIZE,
            aspect="auto",
            xsample=xsample.tolist() if xsample is not None else None,
            ysample=ysample.tolist() if ysample is not None else None,
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
# 1D wiggle 接口适配 — cigvis.plot_multi_traces()
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
    使用 cigvis.plot_multi_traces() 绘制多道 wiggle 图。

    CIGVis 示例（examples/1D/2-plot_multi_traces.py）:
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
    调用 cigvis.plot_multi_traces()。

    CIGVis API:
      plot_multi_traces(data, dt, beg, inter, c, fill_up, fill_down,
                        fill_color, figsize, xlabel, ylabel, save,
                        show, dpi, lw, ax)
    fill_up 是 float 阈值（如 0.2），不是颜色。
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
# 3D 接口适配 — cigvis.create_slices() + cigvis.plot3D()
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
    使用 cigvis 3D API 渲染体数据。

    CIGVis 示例（examples/3Dvispy/01-slice.py）:
      nodes = cigvis.create_slices(volume, cmap='Petrel')
      nodes += cigvis.create_colorbar_from_nodes(nodes, 'Amplitude', select='slices')
      cigvis.plot3D(nodes, view=cigvis.Plot3DView(...), save=cigvis.Plot3DSave(...))
    """
    _require_cigvis()
    if data.ndim != 3:
        raise ValueError("plot3d_volume expects 3D array (nz, ny, nx)")

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

    save_kw = cigvis.Plot3DSave(path=save_path) if save_path else None
    cigvis.plot3D(
        nodes,
        view=cigvis.Plot3DView(size=(800, 600)),
        save=save_kw,
    )
    return nodes


# ---------------------------------------------------------------------------
# SliceViewer 适配 — cigvis.sliceviewer
# ---------------------------------------------------------------------------


def launch_sliceviewer(
    data: NDArray,
    *,
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
) -> Any:
    """
    启动 cigvis SliceViewer 交互式切片浏览器。

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
