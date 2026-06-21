"""MultiMethodCompareSkill：多方法结果对比图。

关键约定（反复强调，防止大模型错误调用）
--------------------------------------
1. 所有 panel 必须使用统一 clim（全局 clim，禁止独立归一化）。
2. 坐标轴必须对齐（相同 extent）。
3. 使用共享 colorbar，而非每个子图各自一个 colorbar。
4. 2x2 布局时 figsize 应适当放大。
5. method_names 与 data_paths 数量必须一致。
"""

from __future__ import annotations

import numpy as np

from geophysics_forward_plotting.backend.adapters import apply_publication_style
from geophysics_forward_plotting.backend.matplotlib_backend import _get_mpl, imshow_panel
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask, PlotStyle
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.axes import extent_from_task
from geophysics_forward_plotting.utils.colors import pick_clim
from geophysics_forward_plotting.utils.export import save_figure


class MultiMethodCompareSkill(BaseSkill):
    """对比 2~4 个方法的结果，统一 clim，共享 colorbar。"""

    def __init__(self) -> None:
        super().__init__(
            name="multi_method_compare",
            description="多方法对比图：统一色标、共享 colorbar、2x2 或横排布局",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.MULTI_METHOD_COMPARISON

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        arrays = list(context.raw_data)
        if not arrays:
            raise DataValidationError("MultiMethodCompareSkill 需要至少一个数组")

        n = len(arrays)
        if n > 4:
            raise DataValidationError("对比图最多支持 4 个方法")

        names = list(task.method_names) or [f"Method {i+1}" for i in range(n)]
        if len(names) < n:
            names += [f"Method {i+1}" for i in range(len(names), n)]

        # 全局 clim（禁止各面板独立归一化）
        all_data = np.concatenate([a.ravel() for a in arrays])
        sym = True if task.symmetric_clim is None else bool(task.symmetric_clim)
        pct = task.clip_percentile or 99.0
        vmin, vmax = pick_clim(all_data, symmetric=sym, clip_percentile=pct)

        style = PlotStyle()
        cmap = task.parameters.get("cmap", style.diverging_cmap if sym else style.sequential_cmap)

        # 布局：1 个用 1x1，2 个用 1x2，3~4 个用 2x2
        ncols = min(n, 2)
        nrows = 1 if n <= 2 else 2
        fw, fh = task.figure_size
        fig_w = fw * ncols + 1.2   # 为 colorbar 预留空间
        fig_h = fh * nrows

        plt = _get_mpl()

        # 用 GridSpec 预留 colorbar 列，避免 tight_layout 后叠加
        gs = plt.GridSpec(
            nrows, ncols + 1,
            width_ratios=[1] * ncols + [0.05],
            wspace=0.3, hspace=0.35,
        )
        fig = plt.figure(figsize=(fig_w, fig_h), dpi=task.dpi)

        axes = []
        for r in range(nrows):
            row_axes = []
            for c in range(ncols):
                row_axes.append(fig.add_subplot(gs[r, c]))
            axes.append(row_axes)

        # 创建 colorbar 专用 axes — 跨所有行的最后一列
        cbar_ax = fig.add_subplot(gs[:, -1])

        dx = task.dx or 1.0
        dz = task.dz or task.dt or 1.0
        nt_or_nz, nx = arrays[0].shape
        ext = extent_from_task(nx=nx, ny=nt_or_nz, dx=dx, dy=dz, x0=task.x0, y0=task.z0)

        last_im = None
        for idx, (arr, name) in enumerate(zip(arrays, names, strict=True)):
            row, col = divmod(idx, ncols)
            ax = axes[row][col]
            im = imshow_panel(
                arr,
                ax=ax,
                extent=ext,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                x_label=task.x_label or "",
                y_label=task.y_label or "",
                title=name,
            )
            last_im = im

        # 隐藏多余子图
        total_slots = nrows * ncols
        for idx in range(n, total_slots):
            row, col = divmod(idx, ncols)
            axes[row][col].set_visible(False)

        # 共享 colorbar
        if last_im is not None:
            from geophysics_forward_plotting.core.defaults import COLORBAR_LABEL_FONT_SIZE, DEFAULT_FONT_SIZE
            cb = fig.colorbar(last_im, cax=cbar_ax)
            cb.set_label(task.colorbar_label or "Amplitude", fontsize=COLORBAR_LABEL_FONT_SIZE)
            cb.ax.tick_params(labelsize=DEFAULT_FONT_SIZE)

        from geophysics_forward_plotting.core.defaults import SUPTITLE_FONT_SIZE
        fig.suptitle(task.title, fontsize=SUPTITLE_FONT_SIZE)
        fig.tight_layout(rect=[0, 0, 1, 0.96])  # 为 suptitle 留空间
        apply_publication_style(fig, style)

        saved = save_figure(
            fig,
            stem="multi_method_compare",
            output_dir=task.output_dir,
            formats=task.export_formats,
            dpi=task.dpi,
        )
        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"多方法对比图已保存至 {[str(p) for p in saved]}",
        )
