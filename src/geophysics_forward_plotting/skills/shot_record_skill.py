"""ShotRecordSkill：绘制炮记录图。

约定
----
- 横轴：Receiver position (km)
- 纵轴：Time (s)，向下
- colormap：diverging（默认 seismic / gray）
- 振幅色标对称
- 多方法对比时必须统一 clim（不允许独立归一化）
"""

from __future__ import annotations

import dataclasses

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


class ShotRecordSkill(BaseSkill):
    """绘制炮记录图（时间向下，振幅对称色标）。"""

    def __init__(self) -> None:
        super().__init__(
            name="shot_record",
            description="绘制炮记录：横轴 Receiver position，纵轴 Time（向下），振幅对称 clim",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.SHOT_RECORD

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        conv = CONVENTIONS[TaskType.SHOT_RECORD]

        updates: dict = {}
        if task.x_label is None:
            updates["x_label"] = conv.x_label
        if task.y_label is None:
            updates["y_label"] = conv.y_label
        if task.colorbar_label is None:
            updates["colorbar_label"] = conv.colorbar_label
        # 炮记录振幅必须对称，除非用户显式设置为 False
        if task.symmetric_clim is None:
            updates["symmetric_clim"] = True
        effective_task = dataclasses.replace(task, **updates) if updates else task

        style = PlotStyle()
        cmap = effective_task.parameters.get("cmap", style.diverging_cmap)

        kwargs = build_imshow_kwargs(
            effective_task,
            context,
            style,
            override_cmap=cmap,
            symmetric=True,
        )

        fig = cigvis_backend.plot2d_image(context.primary(), **kwargs)
        apply_publication_style(fig, style)

        saved = save_figure(
            fig,
            stem="shot_record",
            output_dir=effective_task.output_dir,
            formats=effective_task.export_formats,
            dpi=effective_task.dpi,
        )

        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"炮记录已保存至 {[str(p) for p in saved]}",
        )
