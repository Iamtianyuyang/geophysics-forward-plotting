"""Volume3DSkill：基于 cigvis 显示 3D 地震体数据。

优先使用 cigvis 的 3D vispy 渲染能力。
参考 CIGVis Gallery：
  https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-seismic-volume

如果 cigvis 不可用，给出清晰错误提示，不静默失败。
"""

from __future__ import annotations

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import BackendUnavailableError, DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.colors import pick_clim


class Volume3DSkill(BaseSkill):
    """基于 cigvis 的 3D 体数据切片显示。"""

    def __init__(self) -> None:
        super().__init__(
            name="volume_3d",
            description="3D 地震体多切片显示（cigvis vispy 渲染）",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.VOLUME_3D

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        if not cigvis_backend.is_available():
            raise BackendUnavailableError(
                "Volume3DSkill 需要 cigvis（含 vispy）。\n"
                "请安装：pip install cigvis\n"
                "参考：https://github.com/JintaoLee-Roger/cigvis\n"
                "在无 GUI 环境（如 CI）中请改用 SliceViewer 静态导出。"
            )

        data = context.primary()
        if data.ndim != 3:
            raise DataValidationError(f"Volume3DSkill 期望 3D 数组，得到 shape={data.shape}")

        cmap = task.parameters.get("cmap", "gray")
        sym = task.symmetric_clim if task.symmetric_clim is not None else True
        pct = task.clip_percentile or 99.0
        clim = pick_clim(data, symmetric=sym, clip_percentile=pct)

        slices = task.parameters.get("slices", None)
        if slices is not None:
            slices = tuple(int(s) for s in slices)

        canvas = cigvis_backend.plot3d_volume(
            data,
            cmap=cmap,
            clim=clim,
            slices=slices,
        )

        return FigureResult(
            figure=canvas,
            summary="3D 体数据渲染完成（cigvis canvas），交互式窗口已启动",
        )
