"""Reusable validation helpers kept free of plotting backend details."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import NumericArray


def validate_numeric_array(
    data: np.ndarray,
    *,
    allowed_ndim: Sequence[int] = (1, 2, 3),
    name: str = "data",
) -> NumericArray:
    if not isinstance(data, np.ndarray):
        raise DataValidationError(f"{name} must be a numpy array")
    if data.ndim not in allowed_ndim:
        raise DataValidationError(
            f"{name} has ndim={data.ndim}; expected one of {tuple(allowed_ndim)}"
        )
    if data.size == 0:
        raise DataValidationError(f"{name} must not be empty")
    if not np.issubdtype(data.dtype, np.number):
        raise DataValidationError(f"{name} must use a numeric dtype")
    if not np.isfinite(data).any():
        raise DataValidationError(f"{name} contains no finite values")
    return data


def finite_value_range(data: np.ndarray) -> tuple[float, float]:
    validate_numeric_array(data)
    finite = data[np.isfinite(data)]
    return float(finite.min()), float(finite.max())

