"""DataInspectorSkill：读取数组、推断物理布局、生成 DataContext。"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from geophysics_forward_plotting.core.enums import DataKind, DataLayout, TaskType
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import (
    DataContext,
    FigureResult,
    FigureTask,
)
from geophysics_forward_plotting.skills.base import BaseSkill


def _load_array(path: Path):
    if not path.exists():
        raise DataValidationError(f"数据文件不存在: {path}")
    return np.load(path, allow_pickle=False)


def _infer_layout(shape: tuple[int, ...], task_type: TaskType) -> DataLayout:
    """根据 task_type 和 shape 推断最可能的数组布局。"""
    if len(shape) == 3:
        return DataLayout.NZ_NY_NX
    if len(shape) != 2:
        return DataLayout.UNKNOWN
    a, b = shape
    if task_type in (TaskType.SHOT_RECORD,):
        # 炮记录通常 nt 远大于 nx；若第 0 维更大则认为是 (nt, nx)
        return DataLayout.NT_NX if a >= b else DataLayout.NX_NT
    if task_type in (TaskType.VELOCITY_MODEL, TaskType.WAVEFIELD_SNAPSHOT):
        # 速度模型 / 波场快照：(nz, nx)
        return DataLayout.NZ_NX
    return DataLayout.NZ_NX  # 安全默认值


def _infer_data_kind(task_type: TaskType) -> DataKind:
    mapping = {
        TaskType.VELOCITY_MODEL: DataKind.VELOCITY,
        TaskType.SHOT_RECORD: DataKind.AMPLITUDE,
        TaskType.WAVEFIELD_SNAPSHOT: DataKind.AMPLITUDE,
        TaskType.MULTI_METHOD_COMPARISON: DataKind.AMPLITUDE,
        TaskType.WIGGLE: DataKind.AMPLITUDE,
        TaskType.ERROR_MAP: DataKind.ERROR,
        TaskType.PERFORMANCE: DataKind.PERFORMANCE,
        TaskType.VOLUME_3D: DataKind.VOLUME,
        TaskType.SLICEVIEWER: DataKind.VOLUME,
    }
    return mapping.get(task_type, DataKind.UNKNOWN)


class DataInspectorSkill(BaseSkill):
    """加载并分析所有数据路径，生成 DataContext。"""

    def __init__(self) -> None:
        super().__init__(
            name="data_inspector",
            description="读取 .npy 数据文件，推断维度布局和物理含义",
            priority=99,  # 低优先级——由 PlottingAgent 显式调用，而非路由选择
        )

    def can_handle(self, task: FigureTask) -> bool:
        return True  # 任何任务都需要先做数据检查

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        arrays = []
        for path in task.data_paths:
            arr = _load_array(Path(path))
            arrays.append(arr)

        if not arrays:
            return FigureResult(
                summary="无数据路径，DataContext 为空",
                metadata={"context": DataContext()},
            )

        primary = arrays[0]
        shape = tuple(int(s) for s in primary.shape)
        layout = _infer_layout(shape, TaskType(task.task_type))
        kind = _infer_data_kind(TaskType(task.task_type))
        vmin = float(np.min(primary))
        vmax = float(np.max(primary))

        ctx = DataContext(
            raw_data=tuple(arrays),
            shape=shape,
            ndim=primary.ndim,
            inferred_layout=layout,
            data_kind=kind,
            value_range=(vmin, vmax),
            dataset_names=tuple(str(p.stem) for p in task.data_paths),
        )

        summary = (
            f"加载 {len(arrays)} 个数组，主数组 shape={shape}，"
            f"layout={layout}，kind={kind}，range=[{vmin:.3g}, {vmax:.3g}]"
        )
        return FigureResult(summary=summary, metadata={"context": ctx})
