"""Domain models for plotting requests, inspected data, and results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from geophysics_forward_plotting.core.defaults import (
    DEFAULT_AXIS_LINE_WIDTH,
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_DIVERGING_CMAP,
    DEFAULT_DPI,
    DEFAULT_EXPORT_FORMATS,
    DEFAULT_FIGURE_SIZE,
    DEFAULT_FONT_NAME,
    DEFAULT_FONT_SIZE,
    DEFAULT_LINE_WIDTH,
    DEFAULT_SEQUENTIAL_CMAP,
    SUPPORTED_EXPORT_FORMATS,
)
from geophysics_forward_plotting.core.enums import (
    AxisDirection,
    BackendKind,
    CompareMode,
    DataKind,
    DataLayout,
    TaskType,
)
from geophysics_forward_plotting.core.exceptions import ConfigurationError

NumericArray = NDArray[np.floating[Any] | np.integer[Any]]


@dataclass(frozen=True, slots=True)
class PhysicalAxis:
    """A sampled physical coordinate axis."""

    name: str
    label: str
    unit: str
    sampling: float = 1.0
    origin: float = 0.0
    size: int | None = None
    direction: AxisDirection = AxisDirection.INCREASING

    def __post_init__(self) -> None:
        if self.sampling <= 0:
            raise ConfigurationError(f"Axis {self.name!r} sampling must be positive")
        if self.size is not None and self.size <= 0:
            raise ConfigurationError(f"Axis {self.name!r} size must be positive")

    @property
    def display_label(self) -> str:
        return f"{self.label} ({self.unit})" if self.unit else self.label

    def coordinates(self, size: int | None = None) -> NDArray[np.float64]:
        axis_size = size if size is not None else self.size
        if axis_size is None:
            raise ConfigurationError(f"Axis {self.name!r} requires a size")
        return self.origin + np.arange(axis_size, dtype=float) * self.sampling


@dataclass(slots=True)
class FigureTask:
    """Normalized request consumed by routing and plotting skills."""

    task_type: TaskType | str
    title: str = ""
    data_paths: tuple[Path | str, ...] = ()
    data_options: tuple[dict[str, Any], ...] | Mapping[str, Any] = ()
    output_dir: Path | str = Path("outputs")
    x_label: str | None = None
    y_label: str | None = None
    colorbar_label: str | None = None
    units: dict[str, str] = field(default_factory=dict)
    dx: float | None = None
    dz: float | None = None
    dt: float | None = None
    x0: float = 0.0
    z0: float = 0.0
    t0: float = 0.0
    method_names: tuple[str, ...] = ()
    compare_mode: CompareMode | str = CompareMode.SIDE_BY_SIDE
    symmetric_clim: bool | None = None
    clip_percentile: float | None = 99.0
    figure_size: tuple[float, float] = DEFAULT_FIGURE_SIZE
    dpi: int = DEFAULT_DPI
    export_formats: tuple[str, ...] = DEFAULT_EXPORT_FORMATS
    backend: BackendKind | str = BackendKind.AUTO
    notes: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.task_type = TaskType(self.task_type)
        self.compare_mode = CompareMode(self.compare_mode)
        self.backend = BackendKind(self.backend)
        raw_paths = (
            (self.data_paths,)
            if isinstance(self.data_paths, (str, Path))
            else self.data_paths
        )
        self.data_paths = tuple(Path(path) for path in raw_paths)
        raw_data_options = self.data_options
        if isinstance(raw_data_options, Mapping):
            self.data_options = tuple(dict(raw_data_options) for _ in self.data_paths)
        else:
            self.data_options = tuple(dict(options) for options in raw_data_options)
        if self.data_options and len(self.data_options) != len(self.data_paths):
            raise ConfigurationError(
                "data_options must be one mapping shared by all paths or one mapping per data path"
            )
        self.output_dir = Path(self.output_dir)
        raw_names = (
            (self.method_names,) if isinstance(self.method_names, str) else self.method_names
        )
        self.method_names = tuple(raw_names)
        raw_formats = (
            (self.export_formats,) if isinstance(self.export_formats, str) else self.export_formats
        )
        self.export_formats = tuple(fmt.lower().lstrip(".") for fmt in raw_formats)

        for name, value in (("dx", self.dx), ("dz", self.dz), ("dt", self.dt)):
            if value is not None and value <= 0:
                raise ConfigurationError(f"{name} must be positive when provided")
        if self.dpi <= 0:
            raise ConfigurationError("dpi must be positive")
        if len(self.figure_size) != 2 or any(value <= 0 for value in self.figure_size):
            raise ConfigurationError("figure_size must contain two positive values")
        if self.clip_percentile is not None and not 0 < self.clip_percentile <= 100:
            raise ConfigurationError("clip_percentile must be in (0, 100]")
        unsupported = set(self.export_formats) - SUPPORTED_EXPORT_FORMATS
        if unsupported:
            raise ConfigurationError(f"Unsupported export formats: {sorted(unsupported)}")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> FigureTask:
        return cls(**dict(values))


@dataclass(slots=True)
class DataContext:
    """Data and physical metadata produced by data inspection."""

    raw_data: tuple[NumericArray, ...] = ()
    shape: tuple[int, ...] | None = None
    ndim: int | None = None
    inferred_layout: DataLayout = DataLayout.UNKNOWN
    physical_axes: tuple[PhysicalAxis, ...] = ()
    data_kind: DataKind = DataKind.UNKNOWN
    value_range: tuple[float, float] | None = None
    dataset_names: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def primary(self) -> NumericArray:
        if not self.raw_data:
            raise ConfigurationError("DataContext does not contain any arrays")
        return self.raw_data[0]


@dataclass(slots=True)
class FigureResult:
    """Figure artifact plus export and review metadata."""

    figure: Any | None = None
    saved_paths: list[Path] = field(default_factory=list)
    summary: str = ""
    review_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlotStyle:
    """Shared publication style independent of a plotting backend."""

    font_name: str = DEFAULT_FONT_NAME
    font_size: float = DEFAULT_FONT_SIZE
    line_width: float = DEFAULT_LINE_WIDTH
    axis_line_width: float = DEFAULT_AXIS_LINE_WIDTH
    cmap: str | None = None
    diverging_cmap: str = DEFAULT_DIVERGING_CMAP
    sequential_cmap: str = DEFAULT_SEQUENTIAL_CMAP
    background_color: str = DEFAULT_BACKGROUND_COLOR
    dpi: int = DEFAULT_DPI

    def __post_init__(self) -> None:
        numeric_values: Sequence[float] = (
            self.font_size,
            self.line_width,
            self.axis_line_width,
            self.dpi,
        )
        if any(value <= 0 for value in numeric_values):
            raise ConfigurationError("Style sizes, line widths, and dpi must be positive")
