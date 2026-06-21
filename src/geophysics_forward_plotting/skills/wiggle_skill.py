"""WiggleSkill：绘制地震道 wiggle / wigb 图。

约定
----
- 数据格式：(nt, nx)，时间在第 0 轴
- 时间向下（y 轴倒置）
- 支持 skip / gain / fill_positive 参数
- 适合局部放大对比或整体道展示
"""

from __future__ import annotations

from geophysics_forward_plotting.backend.adapters import (
    apply_publication_style,
    build_wiggle_kwargs,
)
from geophysics_forward_plotting.backend.matplotlib_backend import wiggle_plot
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask, PlotStyle
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.export import save_figure


class WiggleSkill(BaseSkill):
    """绘制地震道 wiggle 图（时间向下，支持 skip/gain/fill）。"""

    def __init__(self) -> None:
        super().__init__(
            name="wiggle",
            description="地震道 wiggle 图：时间向下，支持 skip/gain/fill_positive 参数",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.WIGGLE

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        style = PlotStyle()
        kwargs = build_wiggle_kwargs(task, style)
        fig = wiggle_plot(context.primary(), **kwargs)
        apply_publication_style(fig, style)

        saved = save_figure(
            fig,
            stem="wiggle",
            output_dir=task.output_dir,
            formats=task.export_formats,
            dpi=task.dpi,
        )
        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"Wiggle 图已保存至 {[str(p) for p in saved]}",
        )
