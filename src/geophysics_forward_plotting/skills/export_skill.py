"""ExportSkill：将图件导出为 PNG / PDF / SVG。

默认导出配置
-----------
- PNG：600 dpi（适合投稿）
- PDF / SVG：矢量格式（适合期刊排版）
"""

from __future__ import annotations

from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.export import save_figure


class ExportSkill(BaseSkill):
    """将已有 FigureResult 中的 figure 导出为指定格式。"""

    def __init__(self) -> None:
        super().__init__(
            name="export",
            description="导出图件为 PNG/PDF/SVG，默认 PNG 600 dpi",
            priority=95,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.EXPORT

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        fig = context.metadata.get("figure")
        if fig is None:
            return FigureResult(summary="ExportSkill: 未找到 figure，跳过导出")

        stem = task.parameters.get("stem", "figure")
        saved = save_figure(
            fig,
            stem=stem,
            output_dir=task.output_dir,
            formats=task.export_formats,
            dpi=task.dpi,
        )
        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"图件已导出：{[str(p) for p in saved]}",
        )
