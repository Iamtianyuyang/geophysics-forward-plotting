"""SliceViewerSkill：cigvis SliceViewer 交互式切片浏览。

参考 CIGVis Gallery：
  https://cigvis.readthedocs.io/en/latest/gallery/index.html#sliceviewer

如果 cigvis 不可用，给出清晰错误提示。
"""

from __future__ import annotations

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import BackendUnavailableError, DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.colors import pick_clim


class SliceViewerSkill(BaseSkill):
    """启动 cigvis SliceViewer 交互式 3D 切片浏览器。"""

    def __init__(self) -> None:
        super().__init__(
            name="sliceviewer",
            description="交互式 3D 切片浏览（cigvis SliceViewer）",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.SLICEVIEWER

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        if not cigvis_backend.is_available():
            raise BackendUnavailableError(
                "SliceViewerSkill 需要 cigvis。\n"
                "请安装：pip install cigvis\n"
                "参考：https://cigvis.readthedocs.io/en/latest/gallery/index.html#sliceviewer\n"
                "在无 GUI 环境请改用 volume_3d 静态截图或其他 2D 切片方法。"
            )

        data = context.primary()
        if data.ndim != 3:
            raise DataValidationError(f"SliceViewerSkill 期望 3D 数组，得到 shape={data.shape}")

        cmap = task.parameters.get("cmap", "gray")
        sym = task.symmetric_clim if task.symmetric_clim is not None else False
        pct = task.clip_percentile or 99.0
        clim = pick_clim(data, symmetric=sym, clip_percentile=pct)

        viewer = cigvis_backend.launch_sliceviewer(data, cmap=cmap, clim=clim)

        return FigureResult(
            figure=viewer,
            summary="SliceViewer 已启动，请在交互式窗口中浏览切片",
        )
