"""DataInspectorSkill：读取数组、推断物理布局、生成 DataContext。"""

from __future__ import annotations

import numpy as np

from geophysics_forward_plotting.core.enums import DataKind, DataLayout, TaskType
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.io import load_array_with_metadata
from geophysics_forward_plotting.core.models import (
    DataContext,
    FigureResult,
    FigureTask,
)
from geophysics_forward_plotting.skills.base import BaseSkill


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
            description="读取 NPY/BIN/SEG-Y/SU 数据，推断维度布局和物理含义",
            priority=99,  # 低优先级——由 PlottingAgent 显式调用，而非路由选择
        )

    def can_handle(self, task: FigureTask) -> bool:
        return True  # 任何任务都需要先做数据检查

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        arrays = list(context.raw_data)
        source_metadata: list[dict] = []
        if not arrays:
            for index, path in enumerate(task.data_paths):
                options = task.data_options[index] if task.data_options else {}
                loaded = load_array_with_metadata(path, options)
                arrays.append(loaded.data)
                source_metadata.append(loaded.metadata)

        if not arrays:
            return FigureResult(
                summary="无数据路径，DataContext 为空",
                metadata={"context": DataContext()},
            )

        primary = arrays[0]
        shape = tuple(int(s) for s in primary.shape)
        explicit_layout = task.parameters.get("data_layout")
        source_layout = source_metadata[0].get("data_layout") if source_metadata else None
        if explicit_layout is not None:
            try:
                layout = DataLayout(explicit_layout)
            except ValueError as exc:
                raise DataValidationError(
                    f"Unsupported data_layout={explicit_layout!r}"
                ) from exc
        elif source_layout is not None:
            layout = DataLayout(source_layout)
        elif context.inferred_layout is not DataLayout.UNKNOWN:
            layout = context.inferred_layout
        else:
            layout = _infer_layout(shape, TaskType(task.task_type))
        kind = _infer_data_kind(TaskType(task.task_type))
        vmin = float(np.min(primary))
        vmax = float(np.max(primary))

        metadata = dict(context.metadata)
        if source_metadata:
            metadata["sources"] = source_metadata
            metadata.update(
                {
                    key: source_metadata[0][key]
                    for key in ("format", "sample_interval_s", "sample_interval_us")
                    if key in source_metadata[0]
                }
            )

        ctx = DataContext(
            raw_data=tuple(arrays),
            shape=shape,
            ndim=primary.ndim,
            inferred_layout=layout,
            data_kind=kind,
            value_range=(vmin, vmax),
            dataset_names=(
                context.dataset_names
                or tuple(str(p.stem) for p in task.data_paths)
                or tuple(f"array_{index}" for index in range(len(arrays)))
            ),
            metadata=metadata,
        )

        summary = (
            f"加载 {len(arrays)} 个数组，主数组 shape={shape}，"
            f"layout={layout}，kind={kind}，range=[{vmin:.3g}, {vmax:.3g}]"
        )
        return FigureResult(summary=summary, metadata={"context": ctx})
