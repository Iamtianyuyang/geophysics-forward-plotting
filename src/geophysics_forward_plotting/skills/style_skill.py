"""StyleSkill：将论文级风格参数应用到已有 Figure 上。"""

from __future__ import annotations

from geophysics_forward_plotting.backend.adapters import apply_publication_style
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask, PlotStyle
from geophysics_forward_plotting.skills.base import BaseSkill


class StyleSkill(BaseSkill):
    """从 task.parameters 读取风格参数并应用到图件上。"""

    def __init__(self) -> None:
        super().__init__(
            name="style",
            description="应用论文级风格（字体、线宽、背景色）到已有 Figure",
            priority=90,  # 较低优先级，通常由 agent 显式调用
        )

    def can_handle(self, task: FigureTask) -> bool:
        # StyleSkill 一般由 agent 直接调用，不参与路由
        return False

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        fig = context.metadata.get("figure")
        if fig is None:
            return FigureResult(summary="StyleSkill: 未找到 figure，跳过风格应用")

        style = PlotStyle(
            font_name=task.parameters.get("font_name", "DejaVu Sans"),
            font_size=float(task.parameters.get("font_size", 9.0)),
            line_width=float(task.parameters.get("line_width", 1.0)),
            axis_line_width=float(task.parameters.get("axis_line_width", 0.8)),
            dpi=task.dpi,
        )
        apply_publication_style(fig, style)
        return FigureResult(figure=fig, summary="论文风格已应用")
