"""Configuration and NumPy data loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from geophysics_forward_plotting.core.exceptions import ConfigurationError, DataValidationError
from geophysics_forward_plotting.core.models import FigureTask, NumericArray
from geophysics_forward_plotting.core.validation import validate_numeric_array


def load_array(path: str | Path) -> NumericArray:
    source = Path(path)
    if source.suffix.lower() != ".npy":
        raise DataValidationError(f"Only .npy input is currently supported: {source}")
    if not source.is_file():
        raise DataValidationError(f"Data file does not exist: {source}")
    data = np.load(source, allow_pickle=False)
    return validate_numeric_array(data, name=str(source))


def load_task(path: str | Path) -> FigureTask:
    source = Path(path)
    if not source.is_file():
        raise ConfigurationError(f"Config file does not exist: {source}")
    with source.open("r", encoding="utf-8") as stream:
        values: Any = yaml.safe_load(stream)
    if not isinstance(values, dict):
        raise ConfigurationError("Task config must contain a YAML mapping")
    return FigureTask.from_mapping(values)

