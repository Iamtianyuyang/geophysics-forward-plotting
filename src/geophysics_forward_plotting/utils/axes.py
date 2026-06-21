"""物理轴辅助工具：从采样参数生成坐标数组、推断轴标签。"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def make_axis(n: int, d: float, origin: float = 0.0) -> NDArray:
    """生成均匀采样轴坐标。"""
    return origin + np.arange(n, dtype=float) * d


def extent_from_task(
    *,
    nx: int,
    ny: int,
    dx: float,
    dy: float,
    x0: float = 0.0,
    y0: float = 0.0,
) -> tuple[float, float, float, float]:
    """返回 matplotlib imshow extent=[xmin, xmax, ymax, ymin]（y 轴向下）。"""
    xmax = x0 + (nx - 1) * dx
    ymax = y0 + (ny - 1) * dy
    return (x0, xmax, ymax, y0)
