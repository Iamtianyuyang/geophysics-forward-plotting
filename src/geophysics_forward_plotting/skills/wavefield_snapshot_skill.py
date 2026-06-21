"""WavefieldSnapshotSkill：绘制波场快照图。

约定
----
- 横轴：Distance (km)
- 纵轴：Depth (km)，向下
- 振幅色标对称（diverging）
- 可叠加快照时刻标注（通过 parameters["snapshot_time"]）
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
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask, PlotStyle
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.export import save_figure


class WavefieldSnapshotSkill(BaseSkill):
    """绘制波场快照（深度向下，振幅对称色标）。"""

    def __init__(self) -> None:
        super().__init__(
            name="wavefield_snapshot",
            description="绘制波场快照：深度向下，振幅对称，可标注快照时刻",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.WAVEFIELD_SNAPSHOT

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        conv = CONVENTIONS[TaskType.WAVEFIELD_SNAPSHOT]
        updates: dict = {}
        if task.x_label is None:
            updates["x_label"] = conv.x_label
        if task.y_label is None:
            updates["y_label"] = conv.y_label
        if task.colorbar_label is None:
            updates["colorbar_label"] = conv.colorbar_label
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

        # 叠加快照时刻文字标注
        snap_time = effective_task.parameters.get("snapshot_time")
        if snap_time is not None and fig is not None:
            try:
                ax = fig.axes[0]
                ax.text(
                    0.02,
                    0.05,
                    f"t = {snap_time:.3f} s",
                    transform=ax.transAxes,
                    fontsize=style.font_size,
                    color="white",
                    bbox={"boxstyle": "round,pad=0.2", "fc": "black", "alpha": 0.5},
                )
            except Exception:
                pass  # 非 matplotlib figure 时忽略

        saved = save_figure(
            fig,
            stem="wavefield_snapshot",
            output_dir=effective_task.output_dir,
            formats=effective_task.export_formats,
            dpi=effective_task.dpi,
        )
        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"波场快照已保存至 {[str(p) for p in saved]}",
        )
