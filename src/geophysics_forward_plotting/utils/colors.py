"""颜色工具：对称 clim 计算、colormap 查询。"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def symmetric_clim(data: NDArray, percentile: float = 99.0) -> tuple[float, float]:
    """根据百分位数计算对称色标范围 [-v, +v]。"""
    v = float(np.percentile(np.abs(data), percentile))
    return (-v, v)


def asymmetric_clim(data: NDArray, percentile: float = 99.0) -> tuple[float, float]:
    """非对称范围：用于速度模型等单调数据。"""
    lo = float(np.percentile(data, 100.0 - percentile))
    hi = float(np.percentile(data, percentile))
    return (lo, hi)


def pick_clim(
    data: NDArray,
    *,
    symmetric: bool,
    clip_percentile: float = 99.0,
) -> tuple[float, float]:
    if symmetric:
        return symmetric_clim(data, clip_percentile)
    return asymmetric_clim(data, clip_percentile)
