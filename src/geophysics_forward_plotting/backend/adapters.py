"""Backend 适配层：FigureTask → backend 调用参数。

将 DataContext、FigureTask、PlotStyle 统一转换为 backend 函数所需的
关键词参数，避免在各 Skill 中重复编写相同的参数提取逻辑。
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from geophysics_forward_plotting.core.enums import DataLayout
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureTask, PlotStyle
from geophysics_forward_plotting.utils.axes import extent_from_task
from geophysics_forward_plotting.utils.colors import pick_clim


def build_imshow_kwargs(
    task: FigureTask,
    context: DataContext,
    style: PlotStyle,
    *,
    data: NDArray | None = None,
    override_cmap: str | None = None,
    symmetric: bool | None = None,
) -> dict[str, Any]:
    """
    生成 imshow 风格绘图所需的关键词参数字典。

    返回字段包括：extent, cmap, clim, x_label, y_label, title,
    colorbar_label, figsize, dpi, xsample, ysample。
    """
    import numpy as np

    data = context.primary() if data is None else data
    nt_or_nz, nx = data.shape

    dx = task.dx or 1.0
    inferred_dt = context.metadata.get("sample_interval_s")
    dy = task.dz or task.dt or inferred_dt or 1.0
    ext = extent_from_task(nx=nx, ny=nt_or_nz, dx=dx, dy=dy, x0=task.x0, y0=task.z0 or task.t0)

    sym = symmetric if symmetric is not None else (task.symmetric_clim is True)
    pct = task.clip_percentile or 99.0
    clim = pick_clim(data, symmetric=sym, clip_percentile=pct)

    cmap = override_cmap or style.cmap or (style.diverging_cmap if sym else style.sequential_cmap)

    # 物理坐标数组（供 cigvis.plot2d 的 xsample/ysample 使用）
    x0 = task.x0 or 0.0
    y0 = task.z0 or task.t0 or 0.0
    xsample = np.arange(nx) * dx + x0
    ysample = np.arange(nt_or_nz) * dy + y0

    return {
        "extent": ext,
        "cmap": cmap,
        "clim": clim,
        "x_label": task.x_label or "",
        "y_label": task.y_label or "",
        "title": task.title,
        "colorbar_label": task.colorbar_label or "",
        "figsize": task.figure_size,
        "dpi": task.dpi,
        "xsample": xsample,
        "ysample": ysample,
    }


def build_wiggle_kwargs(
    task: FigureTask,
    style: PlotStyle,
    context: DataContext | None = None,
) -> dict[str, Any]:
    """生成 wiggle_plot 所需的关键词参数。"""
    return {
        "dt": task.dt or (context.metadata.get("sample_interval_s") if context else None) or 0.002,
        "dx": task.dx or 1.0,
        "x0": task.x0,
        "t0": task.t0,
        "skip": int(task.parameters.get("skip", 1)),
        "gain": float(task.parameters.get("gain", 1.0)),
        "scale": float(task.parameters.get("scale", 1.0)),
        "fill_positive": bool(task.parameters.get("fill_positive", True)),
        "x_label": task.x_label or "Distance (km)",
        "y_label": task.y_label or "Time (s)",
        "title": task.title,
        "figsize": task.figure_size,
        "dpi": task.dpi,
    }


def normalize_data_layout(layout: DataLayout | str | None, *, ndim: int) -> DataLayout:
    """Resolve an explicit layout and apply this project's normalized defaults."""
    if layout is None or layout == DataLayout.UNKNOWN or layout == "unknown":
        return DataLayout.NZ_NY_NX if ndim == 3 else DataLayout.NZ_NX
    try:
        return DataLayout(layout)
    except ValueError as exc:
        raise DataValidationError(f"Unsupported data layout: {layout}") from exc


def to_vertical_first_2d(data: NDArray, layout: DataLayout | str | None) -> NDArray:
    """Return a 2D array as (vertical, horizontal), i.e. (nt/nz, nx)."""
    if data.ndim != 2:
        raise DataValidationError(f"Expected a 2D array, got shape={data.shape}")
    resolved = normalize_data_layout(layout, ndim=2)
    if resolved in (DataLayout.NX_NT, DataLayout.NX_NZ):
        return data.T
    if resolved in (DataLayout.NT_NX, DataLayout.NZ_NX):
        return data
    raise DataValidationError(f"Layout {resolved} is not a supported 2D image layout")


def to_cigvis_volume(data: NDArray, layout: DataLayout | str | None) -> NDArray:
    """Adapt a 3D volume to CIGVis line-first order: (x, y, z/time)."""
    if data.ndim != 3:
        raise DataValidationError(f"Expected a 3D volume, got shape={data.shape}")
    resolved = normalize_data_layout(layout, ndim=3)
    if resolved is DataLayout.NZ_NY_NX:
        return np.transpose(data, (2, 1, 0))
    if resolved is DataLayout.NX_NY_NZ:
        return data
    raise DataValidationError(f"Layout {resolved} is not a supported 3D volume layout")


def to_cigvis_surface(data: NDArray, layout: DataLayout | str | None) -> NDArray:
    """Adapt a horizon from (y, x) to the CIGVis (x, y) surface grid."""
    if data.ndim != 2:
        raise DataValidationError(f"Expected a 2D surface, got shape={data.shape}")
    resolved = normalize_data_layout(layout, ndim=3)
    return data.T if resolved is DataLayout.NZ_NY_NX else data


def to_cigvis_position(
    position: tuple[int, int, int] | list[int] | dict[str, Any] | None,
    *,
    shape: tuple[int, int, int],
    layout: DataLayout | str | None,
) -> dict[str, list[int]]:
    """Convert native-layout slice indices to CIGVis x/y/z positions."""
    resolved = normalize_data_layout(layout, ndim=3)
    if position is None:
        nz_or_nx, ny, nx_or_nz = shape
        native = (nz_or_nx // 2, ny // 2, nx_or_nz // 2)
    elif isinstance(position, dict):
        return {
            axis: ([int(value)] if np.isscalar(value) else [int(v) for v in value])
            for axis, value in position.items()
            if axis in {"x", "y", "z"}
        }
    else:
        if len(position) != 3:
            raise DataValidationError("3D slice position must contain three indices")
        native = tuple(int(value) for value in position)

    if resolved is DataLayout.NZ_NY_NX:
        z, y, x = native
    else:
        x, y, z = native
    return {"x": [x], "y": [y], "z": [z]}


def apply_publication_style(fig: Any, style: PlotStyle) -> None:
    """
    将统一论文风格应用到 matplotlib Figure 上。

    字体：Times New Roman (serif) — Geophysics/GJI/SEG 等期刊标准。
    """
    try:
        import matplotlib as mpl

        from geophysics_forward_plotting.core.defaults import (
            DEFAULT_FONT_FAMILY_SANS,
            DEFAULT_FONT_FAMILY_SERIF,
            LABEL_FONT_SIZE,
            SUPTITLE_FONT_SIZE,
            TITLE_FONT_SIZE,
        )

        # 全局字体 — serif 为主 (Times New Roman)，sans-serif 为辅 (Arial)
        mpl.rcParams["font.family"] = "serif"
        mpl.rcParams["font.serif"] = DEFAULT_FONT_FAMILY_SERIF
        mpl.rcParams["font.sans-serif"] = DEFAULT_FONT_FAMILY_SANS
        mpl.rcParams["mathtext.fontset"] = "stix"
        mpl.rcParams["font.size"] = style.font_size
        mpl.rcParams["lines.linewidth"] = style.line_width
        mpl.rcParams["axes.linewidth"] = style.axis_line_width

        for ax in fig.axes:
            ax.tick_params(
                width=style.axis_line_width,
                labelsize=style.font_size,
                pad=4,
            )
            ax.xaxis.label.set_size(LABEL_FONT_SIZE)
            ax.yaxis.label.set_size(LABEL_FONT_SIZE)
            ax.xaxis.labelpad = 6
            ax.yaxis.labelpad = 6

            title = ax.get_title()
            if title:
                ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=8)

        # 总标题 — 使用公共 API
        suptitle = fig._suptitle
        if suptitle is not None:
            suptitle.set_fontsize(SUPTITLE_FONT_SIZE)

    except Exception:
        # 非 matplotlib Figure（如 cigvis canvas）直接跳过
        pass
