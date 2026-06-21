"""CIGVis-first 3D volume skill with explicit domain-to-CIGVis axis mapping."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.backend.adapters import normalize_data_layout
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import (
    BackendUnavailableError,
    DataValidationError,
)
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.utils.colors import pick_clim

_OVERLAY_KEYS = (
    "masks",
    "surfaces",
    "bodies",
    "well_logs",
    "line_logs",
    "points",
    "point_clouds",
    "splats",
    "gaussian_splats",
    "fault_skins",
    "arbitrary_lines",
)


def _load_array(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value
    if isinstance(value, (str, Path)):
        path = Path(value)
        if not path.is_file():
            raise DataValidationError(f"3D overlay file does not exist: {path}")
        return np.load(path, allow_pickle=False)
    return np.asarray(value)


def _as_specs(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (Mapping, str, Path, np.ndarray)):
        return [value]
    return list(value)


def _resolve_overlay_specs(parameters: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    overlays: dict[str, list[dict[str, Any]]] = {}
    for key in _OVERLAY_KEYS:
        resolved: list[dict[str, Any]] = []
        for raw in _as_specs(parameters.get(key)):
            if key == "arbitrary_lines":
                if not isinstance(raw, Mapping):
                    raise DataValidationError(
                        "Arbitrary-line overlays require a mapping with path/anchor options"
                    )
                spec = dict(raw)
                for field in ("data", "volume"):
                    if isinstance(spec.get(field), (str, Path)):
                        spec[field] = _load_array(spec[field])
                resolved.append(spec)
                continue
            if isinstance(raw, Mapping):
                spec = dict(raw)
                reference = spec.pop("path", spec.get("data"))
                if reference is None:
                    raise DataValidationError(f"Overlay '{key}' requires data or path")
                spec["data"] = (
                    str(reference) if key == "fault_skins" else _load_array(reference)
                )
            else:
                spec = {
                    "data": str(raw) if key == "fault_skins" else _load_array(raw)
                }
            resolved.append(spec)
        if resolved:
            overlays[key] = resolved

    # Compatibility aliases used by early YAML examples.
    if parameters.get("fault_path"):
        overlays.setdefault("masks", []).append(
            {
                "data": _load_array(parameters["fault_path"]),
                "cmap": parameters.get("fault_cmap", "jet"),
                "alpha": parameters.get("fault_alpha", 0.5),
                "excpt": "min",
            }
        )
    for horizon_path in _as_specs(parameters.get("horizon_paths")):
        overlays.setdefault("surfaces", []).append(
            {"data": _load_array(horizon_path), "value_type": "depth"}
        )
    return overlays


class Volume3DSkill(BaseSkill):
    """Render a 3D forward-modeling volume through public CIGVis APIs."""

    def __init__(self) -> None:
        super().__init__(
            name="volume_3d",
            description="CIGVis 3D volume slices with scientific overlays and explicit axes",
            priority=10,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.VOLUME_3D

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        if not cigvis_backend.is_available():
            raise BackendUnavailableError(
                "Volume3DSkill requires cigvis and a 3D backend.\n"
                'Install: pip install "cigvis[all]"\n'
                "Gallery: https://cigvis.readthedocs.io/en/latest/gallery/index.html"
            )

        data = context.primary()
        if data.ndim != 3:
            raise DataValidationError(
                f"Volume3DSkill expects a 3D array, got shape={data.shape}"
            )

        parameters = task.parameters
        requested_layout = parameters.get("data_layout", context.inferred_layout)
        layout = normalize_data_layout(requested_layout, ndim=3)
        cmap = str(parameters.get("cmap", "gray"))
        symmetric = task.symmetric_clim if task.symmetric_clim is not None else True
        clim = pick_clim(
            data,
            symmetric=symmetric,
            clip_percentile=task.clip_percentile or 99.0,
        )

        vertical_step = task.dt or task.dz or 1.0
        vertical_origin = task.t0 if task.dt is not None else task.z0
        axis_labels = (
            task.x_label or "Distance (km)",
            str(parameters.get("crossline_label", "Crossline (km)")),
            task.y_label or ("Time (s)" if task.dt is not None else "Depth (km)"),
        )
        intervals = (
            task.dx or 1.0,
            float(parameters.get("dy", task.dx or 1.0)),
            vertical_step,
        )
        starts = (
            task.x0,
            float(parameters.get("y0", 0.0)),
            vertical_origin,
        )

        raw_axis_options = parameters.get("axis")
        axis_options = (
            dict(raw_axis_options) if isinstance(raw_axis_options, Mapping) else None
        )

        save_path_value = parameters.get("save_path")
        if save_path_value is None and parameters.get("save_static"):
            save_path_value = task.output_dir / "volume_3d.png"
        save_path = Path(save_path_value) if save_path_value is not None else None
        if save_path is not None:
            save_path.parent.mkdir(parents=True, exist_ok=True)

        handle = cigvis_backend.plot3d_volume(
            data,
            layout=layout,
            engine=str(parameters.get("engine", "vispy")),
            axis_labels=axis_labels,
            intervals=intervals,
            starts=starts,
            cmap=cmap,
            clim=clim,
            slices=parameters.get("slices"),
            overlays=_resolve_overlay_specs(parameters),
            colorbar_label=task.colorbar_label or "Amplitude",
            display_range=parameters.get("display_range"),
            interpolation=str(parameters.get("interpolation", "cubic")),
            add_axis=bool(parameters.get("add_axis", True)),
            axis_kwargs=axis_options,
            view_kwargs=parameters.get("view"),
            save_path=save_path,
        )

        saved_paths = [save_path] if save_path is not None and save_path.exists() else []
        return FigureResult(
            figure=handle,
            saved_paths=saved_paths,
            summary=(
                f"CIGVis {handle.engine} rendered volume {data.shape} as "
                f"(x, y, z) with layout={layout.value}"
            ),
            metadata={"data_layout": layout.value, "engine": handle.engine},
        )
