"""Review rendered figures against geophysical publication conventions."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from typing import Any

from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill


class FigureReviewSkill(BaseSkill):
    """Check both task configuration and the artists that were rendered."""

    def __init__(self) -> None:
        super().__init__(
            name="figure_review",
            description="Review axes, units, image orientation, color limits, and export DPI",
            priority=80,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.FIGURE_REVIEW

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        messages = self._check_task(task)
        return FigureResult(
            review_messages=messages,
            summary=f"Figure review completed with {len(messages)} message(s)",
        )

    def review(self, result: FigureResult) -> list[str]:
        """Review a completed result; non-Matplotlib handles are skipped."""
        if result.figure is None:
            return []
        messages: list[str] = []
        with suppress(Exception):
            messages.extend(self._check_mpl_figure(result.figure, result.metadata))
        return messages

    def _check_task(self, task: FigureTask) -> list[str]:
        messages: list[str] = []

        if task.colorbar_label is None or not task.colorbar_label.strip():
            messages.append("WARNING: colorbar_label is missing")
        if task.x_label is None or not task.x_label.strip():
            messages.append("WARNING: x_label is missing or has no physical unit")
        if task.y_label is None or not task.y_label.strip():
            messages.append("WARNING: y_label is missing or has no physical unit")
        if task.title and len(task.title) > 60:
            messages.append(
                f"INFO: title has {len(task.title)} characters; consider at most 60"
            )
        if task.dpi < 300:
            messages.append(f"WARNING: DPI={task.dpi} is below the 300 dpi minimum")

        task_type = TaskType(task.task_type)
        if task_type is TaskType.MULTI_METHOD_COMPARISON and task.symmetric_clim is None:
            messages.append(
                "WARNING: comparison does not explicitly request a shared symmetric_clim; "
                "verify that all panels use one global clim"
            )
        if task_type is TaskType.SHOT_RECORD and task.symmetric_clim is False:
            messages.append("WARNING: shot records normally require a symmetric amplitude clim")
        if task_type is TaskType.WAVEFIELD_SNAPSHOT and task.symmetric_clim is False:
            messages.append("WARNING: wavefield snapshots normally require a symmetric clim")
        return messages

    def _check_mpl_figure(self, figure: Any, metadata: dict[str, Any]) -> list[str]:
        messages: list[str] = []
        data_axes = [
            axis
            for axis in figure.axes
            if getattr(axis, "_colorbar", None) is None
            and (axis.images or axis.lines or axis.collections)
        ]

        for axis in data_axes:
            title = axis.get_title() or "untitled"
            if not axis.get_xlabel():
                messages.append(f"WARNING: Axes '{title}' is missing an x-axis label")
            if not axis.get_ylabel():
                messages.append(f"WARNING: Axes '{title}' is missing a y-axis label")

        if metadata.get("expected_y_direction") == "down":
            for axis in data_axes:
                lower, upper = axis.get_ylim()
                if lower <= upper:
                    messages.append(
                        f"ERROR: Axes '{axis.get_title() or 'untitled'}' vertical axis "
                        "is not downward"
                    )

        expected_shapes = _shape_list(metadata.get("expected_image_shapes"))
        rendered_images = [image for axis in data_axes for image in axis.images]
        for index, (image, expected) in enumerate(
            zip(rendered_images, expected_shapes, strict=False)
        ):
            actual = tuple(int(size) for size in image.get_array().shape)
            if actual != expected:
                messages.append(
                    f"ERROR: rendered image {index} has shape {actual}, expected {expected}; "
                    "the data may be transposed"
                )

        if metadata.get("shared_clim") and len(rendered_images) > 1:
            clims = {tuple(float(value) for value in image.get_clim()) for image in rendered_images}
            if len(clims) != 1:
                messages.append("ERROR: comparison panels do not use one shared color limit")
        return messages


def _shape_list(value: Any) -> list[tuple[int, ...]]:
    """Normalize one shape or a sequence of shapes for rendered-image checks."""
    if value is None:
        return []
    if isinstance(value, Sequence) and value and all(isinstance(item, int) for item in value):
        return [tuple(int(item) for item in value)]
    return [tuple(int(item) for item in shape) for shape in value]
