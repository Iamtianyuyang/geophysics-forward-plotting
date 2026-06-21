"""示例：四方法波场对比图（统一 clim，共享 colorbar，2x2 布局）。

比较四种不同方法在 t=500 ms 时刻的波场快照：
  FD-fine    : 精细网格 FDTD 参考解
  FD-coarse  : 粗网格 FDTD（分辨率降低）
  Smoothed   : 高斯低通滤波（模拟低频方法）
  Perturbed  : 速度模型扰动（+5% 随机噪声）
"""

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

arrays = tuple(
    np.load(DATA_DIR / f"method_{m}.npy")
    for m in ("fd_fine", "fd_coarse", "smooth", "perturbed")
)
context = DataContext(raw_data=arrays)

task = FigureTask(
    task_type="multi_method_comparison",
    title="Wavefield Comparison at t = 500 ms",
    output_dir=OUT_DIR,
    method_names=("FD-fine", "FD-coarse", "Smoothed", "Perturbed"),
    dx=0.01,
    dz=0.01,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Amplitude",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(8.0, 6.0),
    export_formats=("png", "pdf"),
    dpi=300,
    parameters={"cmap": "seismic"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
