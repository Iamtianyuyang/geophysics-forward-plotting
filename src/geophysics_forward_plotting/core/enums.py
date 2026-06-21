"""Stable enums shared across tasks, skills, and backends."""

from __future__ import annotations

from enum import StrEnum


class TaskType(StrEnum):
    DATA_INSPECTION = "data_inspection"
    VELOCITY_MODEL = "velocity_model"
    SHOT_RECORD = "shot_record"
    WAVEFIELD_SNAPSHOT = "wavefield_snapshot"
    MULTI_METHOD_COMPARISON = "multi_method_comparison"
    WIGGLE = "wiggle"
    ERROR_MAP = "error_map"
    PERFORMANCE = "performance"
    VOLUME_3D = "volume_3d"
    SLICEVIEWER = "sliceviewer"
    FIGURE_REVIEW = "figure_review"
    EXPORT = "export"


class DataKind(StrEnum):
    UNKNOWN = "unknown"
    VELOCITY = "velocity"
    AMPLITUDE = "amplitude"
    ERROR = "error"
    PERFORMANCE = "performance"
    VOLUME = "volume"


class DataLayout(StrEnum):
    UNKNOWN = "unknown"
    NT_NX = "nt_nx"
    NX_NT = "nx_nt"
    NZ_NX = "nz_nx"
    NX_NZ = "nx_nz"
    NZ_NY_NX = "nz_ny_nx"
    NX_NY_NZ = "nx_ny_nz"


class AxisDirection(StrEnum):
    INCREASING = "increasing"
    DOWNWARD = "downward"


class CompareMode(StrEnum):
    SIDE_BY_SIDE = "side_by_side"
    GRID_2X2 = "grid_2x2"
    DIFFERENCE = "difference"


class ErrorMode(StrEnum):
    SIGNED = "signed"
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class BackendKind(StrEnum):
    AUTO = "auto"
    CIGVIS = "cigvis"
    MATPLOTLIB = "matplotlib"

