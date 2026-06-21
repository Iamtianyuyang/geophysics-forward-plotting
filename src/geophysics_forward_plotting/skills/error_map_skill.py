"""ErrorMapSkill：绘制误差图。

支持三种误差模式
---------------
- signed：有符号误差，使用 diverging colormap
- absolute：绝对误差，使用 sequential colormap
- relative：相对误差（需要 reference，通常为方法 A）

约定
----
- signed error 必须用 diverging cmap（如 seismic / RdBu）
- absolute error 用 sequential cmap（如 viridis / hot）
- colorbar 必须明确标注误差类型和单位
"""

from __future__ import annotations

import numpy as np

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.backend.adapters import (
    apply_publication_style,
    to_vertical_first_2d,
)
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask, PlotStyle
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.axes import extent_from_task
from geophysics_forward_plotting.utils.colors import pick_clim
from geophysics_forward_plotting.utils.export import save_figure


class ErrorMapSkill(BaseSkill):
    """绘制误差图（signed / absolute / relative）。"""

    def __init__(self) -> None:
        super().__init__(
            name="error_map",
            description="误差图：signed 用 diverging cmap，absolute 用 sequential cmap",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.ERROR_MAP

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        if len(context.raw_data) < 2:
            raise DataValidationError("ErrorMapSkill 需要至少两个数组（预测值和参考值）")

        pred = to_vertical_first_2d(
            context.raw_data[0], context.inferred_layout
        ).astype(float)
        ref = to_vertical_first_2d(
            context.raw_data[1], context.inferred_layout
        ).astype(float)

        mode = task.parameters.get("error_mode", "signed")
        if mode == "signed":
            err = pred - ref
        elif mode == "absolute":
            err = np.abs(pred - ref)
        elif mode == "relative":
            denom = np.abs(ref)
            denom[denom < 1e-10] = 1e-10
            err = (pred - ref) / denom
        else:
            raise DataValidationError(f"未知误差模式: {mode}（支持 signed/absolute/relative）")

        style = PlotStyle()
        sym = (mode == "signed")
        cmap = style.diverging_cmap if sym else style.sequential_cmap
        cmap = task.parameters.get("cmap", cmap)
        pct = task.clip_percentile or 99.0
        vmin, vmax = pick_clim(err, symmetric=sym, clip_percentile=pct)

        dx = task.dx or 1.0
        is_time_axis = "time" in (task.y_label or "").lower()
        dz = (task.dt if is_time_axis else task.dz) or task.dz or task.dt or 1.0
        y0 = task.t0 if is_time_axis else task.z0
        nz, nx = err.shape
        ext = extent_from_task(nx=nx, ny=nz, dx=dx, dy=dz, x0=task.x0, y0=y0)
        xsample = np.arange(nx, dtype=float) * dx + task.x0
        ysample = np.arange(nz, dtype=float) * dz + y0

        label_map = {
            "signed": "Signed Error",
            "absolute": "Absolute Error",
            "relative": "Relative Error",
        }
        colorbar_label = task.colorbar_label or label_map[mode]

        fig = cigvis_backend.plot2d_image(
            err,
            extent=ext,
            cmap=cmap,
            clim=(vmin, vmax),
            x_label=task.x_label or "Distance (km)",
            y_label=task.y_label or "Depth (km)",
            title=task.title or f"Error Map ({mode})",
            colorbar_label=colorbar_label,
            figsize=task.figure_size,
            dpi=task.dpi,
            xsample=xsample,
            ysample=ysample,
            downward=True,
        )
        apply_publication_style(fig, style)

        saved = save_figure(
            fig,
            stem=f"error_map_{mode}",
            output_dir=task.output_dir,
            formats=task.export_formats,
            dpi=task.dpi,
        )
        return FigureResult(
            figure=fig,
            saved_paths=saved,
            summary=f"误差图（{mode}）已保存至 {[str(p) for p in saved]}",
            metadata={
                "expected_image_shapes": [err.shape],
                "expected_y_direction": "down",
                "error_mode": mode,
            },
        )
