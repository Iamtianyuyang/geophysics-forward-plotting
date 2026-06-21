"""CIGVis 轻量封装层。

本模块不复制 CIGVis 内部实现，只做接口适配，将本框架的
FigureTask / DataContext 转换为 cigvis 所需的参数格式。

优先参考：
  - CIGVis 仓库：https://github.com/JintaoLee-Roger/cigvis
  - CIGVis Gallery：https://cigvis.readthedocs.io/en/latest/gallery/index.html

分工策略
--------
- 2D 图像切片（速度模型、炮记录、波场快照）：
  cigvis.plot2d 或 cigvis.mpl 接口（当 cigvis 可用时优先使用）。
- 1D 地震道（wiggle / seismogram）：
  cigvis 的 1D trace 接口。
- 3D 体数据渲染（多切片、fault/horizon 叠加）：
  cigvis.plot3d 接口（需要 vispy 环境）。
- SliceViewer（交互式浏览）：
  cigvis.SliceViewer 接口。
- 静态导出：所有 cigvis figure 统一使用 save_figure 工具。

如果 cigvis 不可用，2D/1D 任务会 fallback 到 MatplotlibBackend；
3D / SliceViewer 任务则抛出 BackendUnavailableError，给用户清晰提示。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geophysics_forward_plotting.core.exceptions import BackendUnavailableError

if TYPE_CHECKING:
    from numpy.typing import NDArray

# 延迟导入 cigvis，避免在无 vispy 环境中启动时崩溃
try:
    import cigvis  # type: ignore[import-untyped]

    _CIGVIS_AVAILABLE = True
except ImportError:
    _CIGVIS_AVAILABLE = False


def is_available() -> bool:
    """返回 cigvis 是否可用。"""
    return _CIGVIS_AVAILABLE


def _require_cigvis() -> None:
    if not _CIGVIS_AVAILABLE:
        raise BackendUnavailableError(
            "cigvis is not installed. Install it with: pip install cigvis\n"
            "See: https://github.com/JintaoLee-Roger/cigvis"
        )


# ---------------------------------------------------------------------------
# 2D 接口适配
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
) -> Any:
    """
    使用 cigvis 2D 接口显示图像切片，返回 matplotlib Figure。

    cigvis 已提供丰富的 2D 图件能力，参考：
      https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-image

    如果 cigvis 不可用，自动 fallback 到 matplotlib。
    """
    if _CIGVIS_AVAILABLE:
        return _cigvis_plot2d(
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
        )
    # fallback
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
) -> Any:
    """
    调用 cigvis 的 mpl 2D 绘图接口。

    cigvis 在 mpl 后端提供 cigvis.mpl.plot2d(data, ...) 风格的 API。
    如果具体接口名称随版本变化，在此处集中维护适配。
    """

    # 尝试使用 cigvis 的 mpl 接口；如果接口签名不兼容则回退到纯 matplotlib
    try:
        # cigvis >= 0.2 提供 cigvis.mpl.plot2d
        fig, ax = cigvis.mpl.plot2d(  # type: ignore[attr-defined]
            data,
            figsize=figsize,
            cmap=cmap,
            vmin=clim[0] if clim else None,
            vmax=clim[1] if clim else None,
        )
        if extent is not None:
            im = ax.get_images()[0] if ax.get_images() else None
            if im is not None:
                im.set_extent(extent)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        if colorbar_label:
            cb = fig.colorbar(ax.get_images()[0], ax=ax)
            cb.set_label(colorbar_label)
        return fig
    except AttributeError:
        # cigvis 版本不含 mpl 子模块，回退到纯 matplotlib
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
    cb = fig.colorbar(im, ax=ax)
    if colorbar_label:
        cb.set_label(colorbar_label)
    return fig


# ---------------------------------------------------------------------------
# 3D 接口适配
# ---------------------------------------------------------------------------


def plot3d_volume(
    data: NDArray,
    *,
    axis_labels: tuple[str, str, str] = ("X", "Y", "Z"),
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
    slices: tuple[int, int, int] | None = None,
) -> Any:
    """
    使用 cigvis 3D vispy 接口显示体数据。

    cigvis 提供的 3D 能力（参考 Gallery）包括：
      - 多切片显示
      - fault / horizon / RGT overlay
      - 点云 / 井轨迹

    需要 vispy 环境（通常需要 GUI 桌面）。
    """
    _require_cigvis()
    nx, ny, nz = data.shape if data.ndim == 3 else (0, 0, 0)
    if data.ndim != 3:
        raise ValueError("plot3d_volume 期望 3D 数组 (nz, ny, nx)")

    ni, nj, nk = data.shape
    sx, sy, sz = slices or (ni // 2, nj // 2, nk // 2)

    # cigvis.plot3d 是 cigvis 的高层 3D 接口
    # 参数随 cigvis 版本可能调整，在此集中维护
    canvas = cigvis.plot3d(  # type: ignore[attr-defined]
        data,
        pos=[sx, sy, sz],
        cmap=cmap,
        clim=clim,
        return_canvas=True,
    )
    return canvas


# ---------------------------------------------------------------------------
# SliceViewer 适配
# ---------------------------------------------------------------------------


def launch_sliceviewer(
    data: NDArray,
    *,
    cmap: str = "gray",
    clim: tuple[float, float] | None = None,
) -> Any:
    """
    启动 cigvis SliceViewer 交互式切片浏览器。

    参考 CIGVis Gallery：
      https://cigvis.readthedocs.io/en/latest/gallery/index.html#sliceviewer

    无法在无 GUI 环境（如 CI 流水线）中运行，运行前请检查 is_available()。
    """
    _require_cigvis()
    viewer = cigvis.SliceViewer(  # type: ignore[attr-defined]
        data,
        cmap=cmap,
        clim=clim,
    )
    viewer.show()
    return viewer
