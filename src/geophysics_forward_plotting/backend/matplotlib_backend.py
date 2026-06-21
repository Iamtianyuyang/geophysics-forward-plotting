"""Matplotlib backend：处理 cigvis 不擅长的统计图和补充绘图。

适用场景
--------
- 性能对比图（柱状图、折线图）
- 误差曲线
- wiggle / wigb 地震道图（cigvis 1D 接口 fallback）
- 多子图对比布局
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def _get_mpl():
    """延迟导入 matplotlib，提供清晰的缺失提示。"""
    try:
        import matplotlib.pyplot as plt

        return plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib 未安装，请执行：pip install matplotlib\n"
            "或：pip install 'geophysics-forward-plotting[plot]'"
        ) from exc


def bar_chart(
    categories: list[str],
    values: list[float],
    *,
    ylabel: str = "",
    title: str = "",
    color: str = "#4C72B0",
    figsize: tuple[float, float] = (6.0, 4.0),
    dpi: int = 600,
) -> Any:
    """绘制单系列柱状图，适合时间/内存/加速比对比。"""
    from geophysics_forward_plotting.core.defaults import (
        LABEL_FONT_SIZE,
        TITLE_FONT_SIZE,
    )

    # 从 ylabel 提取单位后缀（如 "Time (s)" → "s"）
    unit = ""
    if "(" in ylabel and ")" in ylabel:
        unit = ylabel[ylabel.index("(") + 1 : ylabel.index(")")]

    plt = _get_mpl()
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    x = np.arange(len(categories))

    colors = plt.cm.Blues(np.linspace(0.4, 0.85, len(categories)))
    bars = ax.bar(
        x, values, width=0.55, color=colors,
        edgecolor="#2c3e50", linewidth=0.6, zorder=3,
    )

    for bar, val in zip(bars, values, strict=True):
        label = f"{val:.3f} {unit}" if unit else f"{val:.3f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.03,
            label,
            ha="center", va="bottom", fontsize=9, fontweight="bold",
            color="#2c3e50",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=LABEL_FONT_SIZE)
    ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=14)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(width=0.6, labelsize=10)
    ax.set_ylim(0, max(values) * 1.22)
    ax.grid(axis="y", alpha=0.25, linestyle="--", color="#7f8c8d", zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def multi_bar_chart(
    categories: list[str],
    series: dict[str, list[float]],
    *,
    ylabel: str = "",
    title: str = "",
    figsize: tuple[float, float] = (8.0, 4.5),
    dpi: int = 600,
) -> Any:
    """绘制多系列分组柱状图（多方法性能对比）。"""
    plt = _get_mpl()
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    n_series = len(series)
    n_groups = len(categories)
    x = np.arange(n_groups)
    width = 0.7 / n_series
    for i, (label, vals) in enumerate(series.items()):
        offset = (i - n_series / 2 + 0.5) * width
        ax.bar(x + offset, vals, width=width, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=15, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(framealpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return fig


def wiggle_plot(
    data: NDArray,
    *,
    dt: float = 0.002,
    dx: float = 1.0,
    x0: float = 0.0,
    t0: float = 0.0,
    skip: int = 1,
    gain: float = 1.0,
    fill_positive: bool = True,
    color: str = "black",
    x_label: str = "Distance (km)",
    y_label: str = "Time (s)",
    title: str = "",
    figsize: tuple[float, float] = (7.0, 6.0),
    dpi: int = 600,
) -> Any:
    """
    绘制地震道 wiggle 图。

    data: (nt, nx) 数组，时间在第 0 轴，道在第 1 轴。
    y 轴向下（时间增大向下）。
    """
    from geophysics_forward_plotting.core.defaults import LABEL_FONT_SIZE, TITLE_FONT_SIZE

    plt = _get_mpl()
    nt, nx = data.shape
    t = t0 + np.arange(nt) * dt
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    for ix in range(0, nx, skip):
        x_center = x0 + ix * dx
        trace = gain * data[:, ix]
        scale = dx * 0.9 / (np.max(np.abs(trace)) + 1e-9)
        xvals = x_center + trace * scale
        ax.plot(xvals, t, color=color, linewidth=0.5)
        if fill_positive:
            ax.fill_betweenx(t, x_center, xvals, where=(xvals > x_center), color=color, alpha=0.8)

    ax.set_xlim(x0 - dx, x0 + nx * dx)
    ax.set_xlabel(x_label, fontsize=LABEL_FONT_SIZE)
    ax.set_ylabel(y_label, fontsize=LABEL_FONT_SIZE)
    ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=8)
    ax.tick_params(labelsize=10)
    ax.invert_yaxis()
    return fig


def imshow_panel(
    data: NDArray,
    *,
    ax: Any,
    extent: tuple[float, float, float, float] | None = None,
    cmap: str = "seismic",
    vmin: float | None = None,
    vmax: float | None = None,
    x_label: str = "",
    y_label: str = "",
    title: str = "",
) -> Any:
    """在已有 Axes 上绘制图像，返回 AxesImage（供共享 colorbar 使用）。"""
    from geophysics_forward_plotting.core.defaults import LABEL_FONT_SIZE, TITLE_FONT_SIZE

    im = ax.imshow(
        data,
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        origin="upper",
    )
    ax.set_xlabel(x_label, fontsize=LABEL_FONT_SIZE)
    ax.set_ylabel(y_label, fontsize=LABEL_FONT_SIZE)
    ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=6)
    ax.tick_params(labelsize=10)
    return im
