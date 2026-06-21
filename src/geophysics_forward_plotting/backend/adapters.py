"""Backend 适配层：FigureTask → backend 调用参数。

将 DataContext、FigureTask、PlotStyle 统一转换为 backend 函数所需的
关键词参数，避免在各 Skill 中重复编写相同的参数提取逻辑。
"""

from __future__ import annotations

from typing import Any

from geophysics_forward_plotting.core.models import DataContext, FigureTask, PlotStyle
from geophysics_forward_plotting.utils.axes import extent_from_task
from geophysics_forward_plotting.utils.colors import pick_clim


def build_imshow_kwargs(
    task: FigureTask,
    context: DataContext,
    style: PlotStyle,
    *,
    override_cmap: str | None = None,
    symmetric: bool | None = None,
) -> dict[str, Any]:
    """
    生成 imshow 风格绘图所需的关键词参数字典。

    返回字段包括：extent, cmap, clim, x_label, y_label, title,
    colorbar_label, figsize, dpi。
    """
    data = context.primary()
    nt_or_nz, nx = data.shape

    dx = task.dx or 1.0
    dy = task.dz or task.dt or 1.0
    ext = extent_from_task(nx=nx, ny=nt_or_nz, dx=dx, dy=dy, x0=task.x0, y0=task.z0 or task.t0)

    sym = symmetric if symmetric is not None else (task.symmetric_clim is True)
    pct = task.clip_percentile or 99.0
    clim = pick_clim(data, symmetric=sym, clip_percentile=pct)

    cmap = override_cmap or style.cmap or (style.diverging_cmap if sym else style.sequential_cmap)

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
    }


def build_wiggle_kwargs(task: FigureTask, style: PlotStyle) -> dict[str, Any]:
    """生成 wiggle_plot 所需的关键词参数。"""
    return {
        "dt": task.dt or 0.002,
        "dx": task.dx or 1.0,
        "x0": task.x0,
        "t0": task.t0,
        "skip": int(task.parameters.get("skip", 1)),
        "gain": float(task.parameters.get("gain", 1.0)),
        "fill_positive": bool(task.parameters.get("fill_positive", True)),
        "x_label": task.x_label or "Distance (km)",
        "y_label": task.y_label or "Time (s)",
        "title": task.title,
        "figsize": task.figure_size,
        "dpi": task.dpi,
    }


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
