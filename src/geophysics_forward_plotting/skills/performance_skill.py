"""PerformanceSkill：绘制性能对比图（时间、内存、加速比）。

设计原则
--------
- 使用 matplotlib（cigvis 不擅长纯统计图）
- 柱状图默认，支持折线图（通过 parameters["chart_type"]）
- 明确标注 baseline
- 支持多系列（多方法）
- 适合论文 Table / Figure
"""

from __future__ import annotations

from geophysics_forward_plotting.backend.adapters import apply_publication_style
from geophysics_forward_plotting.backend.matplotlib_backend import (
    bar_chart,
    multi_bar_chart,
)
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask, PlotStyle
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.export import save_figure


class PerformanceSkill(BaseSkill):
    """绘制时间/内存/加速比性能对比图。"""

    def __init__(self) -> None:
        super().__init__(
            name="performance",
            description="性能对比图（柱状图）：时间/内存/加速比，明确 baseline",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.PERFORMANCE

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        params = task.parameters

        # 数据来源：从 parameters 中读取，或从 DataContext 中读取 1D 数组
        categories = params.get("categories") or list(task.method_names) or []
        if not categories:
            raise DataValidationError(
                "PerformanceSkill 需要 categories（方法名列表）"
                " 通过 task.parameters['categories'] 或 task.method_names 传入"
            )

        metric_label = params.get("metric_label", "Time (s)")
        style = PlotStyle()

        # 单系列模式：parameters["values"] = [v1, v2, ...]
        if "values" in params:
            values = [float(v) for v in params["values"]]
            if len(values) != len(categories):
                raise DataValidationError("categories 和 values 长度必须相同")
            fig = bar_chart(
                categories,
                values,
                ylabel=metric_label,
                title=task.title,
                figsize=task.figure_size,
                dpi=task.dpi,
            )
        # 多系列模式：parameters["series"] = {"Method A": [v1,v2,...], ...}
        elif "series" in params:
            series: dict = {k: [float(x) for x in v] for k, v in params["series"].items()}
            fig = multi_bar_chart(
                categories,
                series,
                ylabel=metric_label,
                title=task.title,
                figsize=task.figure_size,
                dpi=task.dpi,
            )
        else:
            raise DataValidationError(
                "PerformanceSkill 需要 parameters['values']（单系列）"
                " 或 parameters['series']（多系列）"
            )

        apply_publication_style(fig, style)
        saved = save_figure(
            fig,
            stem="performance",
            output_dir=task.output_dir,
            formats=task.export_formats,
            dpi=task.dpi,
        )
        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"性能图已保存至 {[str(p) for p in saved]}",
        )
