"""VelocityModelSkill：绘制速度模型（论文级）。

约定
----
- 横轴：Distance (km)
- 纵轴：Depth (km)，向下
- colorbar：Velocity (m/s)
- colormap：非对称，默认 jet 或用户指定
- 不对称色标（速度单调增大）
"""

from __future__ import annotations

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.backend.adapters import (
    apply_publication_style,
    build_imshow_kwargs,
)
from geophysics_forward_plotting.core.conventions import CONVENTIONS
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.models import (
    DataContext,
    FigureResult,
    FigureTask,
    PlotStyle,
)
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.export import save_figure


class VelocityModelSkill(BaseSkill):
    """绘制速度模型图。"""

    def __init__(self) -> None:
        super().__init__(
            name="velocity_model",
            description=(
                "绘制速度模型：横轴 Distance，纵轴 Depth（向下），"
                "colorbar 标注 Velocity (m/s)"
            ),
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.VELOCITY_MODEL

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        conv = CONVENTIONS[TaskType.VELOCITY_MODEL]

        # 应用约定默认值（允许任务覆盖）
        effective_task = _apply_convention_defaults(task, conv)
        style = PlotStyle()

        kwargs = build_imshow_kwargs(
            effective_task,
            context,
            style,
            override_cmap=effective_task.parameters.get("cmap", "jet"),
            symmetric=False,  # 速度模型非对称
        )

        fig = cigvis_backend.plot2d_image(context.primary(), **kwargs)
        apply_publication_style(fig, style)

        saved = save_figure(
            fig,
            stem="velocity_model",
            output_dir=effective_task.output_dir,
            formats=effective_task.export_formats,
            dpi=effective_task.dpi,
        )

        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"速度模型已保存至 {[str(p) for p in saved]}",
        )


def _apply_convention_defaults(task: FigureTask, conv) -> FigureTask:
    """将地球物理约定作为默认值填入 task（不覆盖用户已设定的值）。"""
    import dataclasses

    updates: dict = {}
    if task.x_label is None:
        updates["x_label"] = conv.x_label
    if task.y_label is None:
        updates["y_label"] = conv.y_label
    if task.colorbar_label is None:
        updates["colorbar_label"] = conv.colorbar_label
    if task.symmetric_clim is None:
        updates["symmetric_clim"] = conv.symmetric_clim
    if updates:
        return dataclasses.replace(task, **updates)
    return task
