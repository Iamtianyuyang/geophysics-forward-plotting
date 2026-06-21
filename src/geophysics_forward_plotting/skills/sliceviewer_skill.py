"""Interactive CIGVis SliceViewer skill using create_slice/add_mask/show."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.backend.adapters import normalize_data_layout
from geophysics_forward_plotting.core.enums import DataLayout, TaskType
from geophysics_forward_plotting.core.exceptions import (
    BackendUnavailableError,
    DataValidationError,
)
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.colors import pick_clim


def _load_mask_specs(raw_masks: Any) -> list[dict[str, Any]]:
    if raw_masks is None:
        return []
    values = [raw_masks] if isinstance(raw_masks, (Mapping, str, Path)) else list(raw_masks)
    masks: list[dict[str, Any]] = []
    for raw in values:
        spec = dict(raw) if isinstance(raw, Mapping) else {"path": raw}
        reference = spec.pop("path", spec.pop("data", None))
        if reference is None:
            raise DataValidationError("SliceViewer mask requires data or path")
        if isinstance(reference, (str, Path)):
            reference = np.load(Path(reference), allow_pickle=False)
        spec["data"] = np.asarray(reference)
        spec.setdefault("cmap", "jet")
        spec.setdefault("alpha", 0.45)
        spec.setdefault("excpt", "min")
        masks.append(spec)
    return masks


class SliceViewerSkill(BaseSkill):
    """Launch a browser-based 2D slice explorer for 3D forward data."""

    def __init__(self) -> None:
        super().__init__(
            name="sliceviewer",
            description="CIGVis SliceViewer with overlays and comparison grids",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.SLICEVIEWER

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        if not cigvis_backend.is_available():
            raise BackendUnavailableError(
                'SliceViewerSkill requires: pip install "cigvis[sliceviewer]"'
            )
        if not context.raw_data or any(array.ndim != 3 for array in context.raw_data):
            shapes = [array.shape for array in context.raw_data]
            raise DataValidationError(f"SliceViewer expects 3D arrays, got {shapes}")

        parameters = task.parameters
        layout = normalize_data_layout(
            parameters.get("data_layout", context.inferred_layout),
            ndim=3,
        )
        if layout is DataLayout.NZ_NY_NX:
            default_display_axes = (0, 2)
            default_labels = ("Depth", "Crossline", "Distance")
        else:
            default_display_axes = (2, 0)
            default_labels = ("Distance", "Crossline", "Depth")

        primary = context.primary()
        symmetric = task.symmetric_clim if task.symmetric_clim is not None else False
        clim = pick_clim(
            primary,
            symmetric=symmetric,
            clip_percentile=task.clip_percentile or 99.0,
        )
        display_axes = tuple(parameters.get("display_axes", default_display_axes))
        axis_labels = tuple(parameters.get("axis_labels", default_labels))

        show_kwargs = dict(parameters.get("show_options", {}))
        if task.title:
            show_kwargs.setdefault("title", task.title)
        if "port" in parameters:
            show_kwargs.setdefault("port", int(parameters["port"]))
        if "plot_height" in parameters:
            show_kwargs.setdefault("plot_height", int(parameters["plot_height"]))

        handle = cigvis_backend.launch_sliceviewer(
            primary,
            comparison_data=context.raw_data[1:],
            cmap=str(parameters.get("cmap", "gray")),
            clim=clim,
            display_axes=(int(display_axes[0]), int(display_axes[1])),
            indices=parameters.get("indices"),
            axis_labels=axis_labels,
            aspect=parameters.get("aspect", "auto"),
            interpolation=str(parameters.get("interpolation", "nearest")),
            render_mode=str(parameters.get("render_mode", "float")),
            masks=_load_mask_specs(parameters.get("masks")),
            annotations=parameters.get("annotations", ()),
            grid=tuple(parameters["grid"]) if "grid" in parameters else None,
            show=bool(parameters.get("show", True)),
            show_kwargs=show_kwargs,
        )
        return FigureResult(
            figure=handle,
            summary=(
                f"CIGVis SliceViewer prepared {len(context.raw_data)} volume(s), "
                f"display_axes={display_axes}, layout={layout.value}"
            ),
            metadata={"data_layout": layout.value, "display_axes": display_axes},
        )
