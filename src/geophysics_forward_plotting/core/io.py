"""Configuration and scientific-array loading utilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from geophysics_forward_plotting.core.exceptions import ConfigurationError, DataValidationError
from geophysics_forward_plotting.core.models import FigureTask, NumericArray
from geophysics_forward_plotting.core.validation import validate_numeric_array

_SEGY_SUFFIXES = {".sgy", ".segy"}


@dataclass(frozen=True, slots=True)
class LoadedArray:
    """Loaded numeric data and provenance extracted from its source format."""

    data: NumericArray
    metadata: dict[str, Any]


def load_array(path: str | Path, options: Mapping[str, Any] | None = None) -> NumericArray:
    """Load a NumPy, raw binary, SEG-Y, or SU file as a numeric array."""
    return load_array_with_metadata(path, options).data


def load_array_with_metadata(
    path: str | Path,
    options: Mapping[str, Any] | None = None,
) -> LoadedArray:
    """Load an array and retain format-specific sampling metadata."""
    source = Path(path)
    if not source.is_file():
        raise DataValidationError(f"Data file does not exist: {source}")

    normalized_options = dict(options or {})
    suffix = source.suffix.lower()
    if suffix == ".npy":
        data = np.load(source, allow_pickle=False)
        metadata = {"format": "npy"}
    elif suffix == ".bin":
        data, metadata = _load_binary(source, normalized_options)
    elif suffix in _SEGY_SUFFIXES or suffix == ".su":
        data, metadata = _load_seismic(source, normalized_options, is_su=suffix == ".su")
    else:
        supported = ".npy, .bin, .sgy, .segy, .su"
        raise DataValidationError(f"Unsupported data format '{suffix}'; expected {supported}")

    validated = validate_numeric_array(np.asarray(data), name=str(source))
    metadata.update(
        {
            "path": str(source),
            "shape": tuple(int(size) for size in validated.shape),
            "dtype": str(validated.dtype),
        }
    )
    return LoadedArray(data=validated, metadata=metadata)


def _load_binary(source: Path, options: Mapping[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    shape_value = options.get("shape")
    if shape_value is None:
        raise DataValidationError(
            f"Raw binary input requires data_options.shape: {source}"
        )
    try:
        shape = tuple(int(size) for size in shape_value)
    except (TypeError, ValueError) as exc:
        raise DataValidationError("Binary shape must be a sequence of integers") from exc
    if not shape or any(size == 0 or size < -1 for size in shape) or shape.count(-1) > 1:
        raise DataValidationError(f"Invalid binary shape: {shape}")

    try:
        dtype = np.dtype(options.get("dtype", "float32"))
    except (TypeError, ValueError) as exc:
        raise DataValidationError(f"Invalid binary dtype: {options.get('dtype')!r}") from exc
    endianness = str(options.get("endianness", "native")).lower()
    byte_orders = {"native": "=", "little": "<", "big": ">"}
    if endianness not in byte_orders:
        raise DataValidationError("Binary endianness must be native, little, or big")
    if dtype.itemsize > 1:
        dtype = dtype.newbyteorder(byte_orders[endianness])

    order = str(options.get("order", "C")).upper()
    if order not in {"C", "F"}:
        raise DataValidationError("Binary order must be C or F")
    offset = int(options.get("offset", 0))
    if offset < 0:
        raise DataValidationError("Binary offset must be non-negative")

    raw = np.fromfile(source, dtype=dtype, offset=offset)
    try:
        data = raw.reshape(shape, order=order)
    except ValueError as exc:
        raise DataValidationError(
            f"Binary file has {raw.size} values and cannot be reshaped to {shape}"
        ) from exc
    metadata = {
        "format": "bin",
        "endianness": endianness,
        "order": order,
        "offset": offset,
    }
    if "data_layout" in options:
        metadata["data_layout"] = str(options["data_layout"])
    return data, metadata


def _load_seismic(
    source: Path,
    options: Mapping[str, Any],
    *,
    is_su: bool,
) -> tuple[np.ndarray, dict[str, Any]]:
    try:
        import segyio  # type: ignore[import-untyped]
    except ImportError as exc:
        raise DataValidationError(
            f"Reading {source.suffix} requires segyio. Install: conda install -c conda-forge segyio"
        ) from exc

    opener = segyio.su.open if is_su else segyio.open
    open_kwargs: dict[str, Any] = {
        "mode": "r",
        "strict": bool(options.get("strict", False)),
        "ignore_geometry": bool(options.get("ignore_geometry", True)),
    }
    if "endian" in options:
        endian = str(options["endian"]).lower()
        if endian not in {"big", "little"}:
            raise DataValidationError("SEG-Y/SU endian must be big or little")
        open_kwargs["endian"] = endian

    try:
        with opener(str(source), **open_kwargs) as seismic:
            if bool(options.get("mmap", True)) and hasattr(seismic, "mmap"):
                seismic.mmap()
            traces = np.asarray(seismic.trace.raw[:]).copy()
            samples = np.asarray(getattr(seismic, "samples", ()), dtype=float)
            sample_interval_us = _segy_sample_interval_us(segyio, seismic)
    except Exception as exc:
        raise DataValidationError(f"Failed to read seismic file {source}: {exc}") from exc

    if traces.ndim != 2:
        raise DataValidationError(
            f"Expected trace-major 2D seismic data, got shape={traces.shape}"
        )
    output_layout = str(options.get("output_layout", "samples_traces")).lower()
    if output_layout == "samples_traces":
        data = traces.T
        data_layout = "nt_nx"
    elif output_layout == "traces_samples":
        data = traces
        data_layout = "nx_nt"
    else:
        raise DataValidationError(
            "SEG-Y/SU output_layout must be samples_traces or traces_samples"
        )

    output_shape = options.get("shape")
    if output_shape is not None:
        try:
            resolved_shape = tuple(int(size) for size in output_shape)
            output_order = str(options.get("order", "C")).upper()
            data = data.reshape(resolved_shape, order=output_order)
        except (TypeError, ValueError) as exc:
            raise DataValidationError(
                f"Seismic samples cannot be reshaped to {output_shape}"
            ) from exc
        if data.ndim == 3:
            data_layout = str(options.get("data_layout", "nz_ny_nx"))
    elif "data_layout" in options:
        data_layout = str(options["data_layout"])

    metadata: dict[str, Any] = {
        "format": "su" if is_su else "segy",
        "source_trace_layout": "traces_samples",
        "output_layout": output_layout,
        "data_layout": data_layout,
        "trace_count": int(traces.shape[0]),
        "sample_count": int(traces.shape[1]),
    }
    if samples.size:
        metadata["sample_coordinates"] = samples
    if sample_interval_us is not None and sample_interval_us > 0:
        metadata["sample_interval_us"] = sample_interval_us
        metadata["sample_interval_s"] = sample_interval_us * 1e-6
    return data, metadata


def _segy_sample_interval_us(segyio_module: Any, seismic: Any) -> float | None:
    try:
        value = float(segyio_module.tools.dt(seismic, fallback_dt=0.0))
    except (AttributeError, TypeError, ValueError):
        try:
            value = float(segyio_module.tools.dt(seismic))
        except (AttributeError, TypeError, ValueError):
            return None
    return value or None


def load_task(path: str | Path) -> FigureTask:
    source = Path(path)
    if not source.is_file():
        raise ConfigurationError(f"Config file does not exist: {source}")
    with source.open("r", encoding="utf-8") as stream:
        values: Any = yaml.safe_load(stream)
    if not isinstance(values, dict):
        raise ConfigurationError("Task config must contain a YAML mapping")
    return FigureTask.from_mapping(values)
