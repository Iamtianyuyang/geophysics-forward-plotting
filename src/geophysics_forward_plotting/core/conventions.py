"""地球物理图件的轴、色标、方向约定。

这些约定由 FigureReviewSkill 强制执行，并在各 Skill 中作为默认值使用。
"""

from __future__ import annotations

from dataclasses import dataclass

from geophysics_forward_plotting.core.enums import AxisDirection, DataKind, TaskType


@dataclass(frozen=True, slots=True)
class PlotConvention:
    x_label: str
    y_label: str
    colorbar_label: str
    y_direction: AxisDirection
    data_kind: DataKind
    symmetric_clim: bool


CONVENTIONS: dict[TaskType, PlotConvention] = {
    TaskType.VELOCITY_MODEL: PlotConvention(
        x_label="Distance (km)",
        y_label="Depth (km)",
        colorbar_label="Velocity (m/s)",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.VELOCITY,
        symmetric_clim=False,
    ),
    TaskType.SHOT_RECORD: PlotConvention(
        x_label="Receiver position (km)",
        y_label="Time (s)",
        colorbar_label="Amplitude",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.AMPLITUDE,
        symmetric_clim=True,
    ),
    TaskType.WAVEFIELD_SNAPSHOT: PlotConvention(
        x_label="Distance (km)",
        y_label="Depth (km)",
        colorbar_label="Amplitude",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.AMPLITUDE,
        symmetric_clim=True,
    ),
    TaskType.MULTI_METHOD_COMPARISON: PlotConvention(
        x_label="Distance (km)",
        y_label="Depth (km)",
        colorbar_label="Amplitude",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.AMPLITUDE,
        symmetric_clim=True,
    ),
    TaskType.WIGGLE: PlotConvention(
        x_label="Distance (km)",
        y_label="Time (s)",
        colorbar_label="",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.AMPLITUDE,
        symmetric_clim=True,
    ),
    TaskType.ERROR_MAP: PlotConvention(
        x_label="Distance (km)",
        y_label="Depth (km)",
        colorbar_label="Signed Error",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.ERROR,
        symmetric_clim=True,
    ),
    TaskType.VOLUME_3D: PlotConvention(
        x_label="Distance (km)",
        y_label="Depth (km)",
        colorbar_label="Amplitude",
        y_direction=AxisDirection.DOWNWARD,
        data_kind=DataKind.VOLUME,
        symmetric_clim=True,
    ),
}


def convention_for(task_type: TaskType | str) -> PlotConvention | None:
    return CONVENTIONS.get(TaskType(task_type))
