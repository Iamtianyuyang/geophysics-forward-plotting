"""示例：四方法波场对比图（统一 clim，共享 colorbar，2x2 布局）。

比较四种不同方法在 t=500 ms 时刻的波场快照：
  Pseudo-Spectral : 伪谱法参考解（谱精度空间导数）
  Deepwave        : deepwave 声波正演（dx=10m）
  Coarse          : deepwave 粗网格（dx=20m，分辨率降低）
  Smoothed        : 高斯低通滤波（模拟低频方法）
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

_REQUIRED = ["method_ps_ref.npy", "method_deepwave.npy", "method_coarse.npy", "method_smooth.npy"]
_missing = [f for f in _REQUIRED if not (DATA_DIR / f).exists()]
if _missing:
    print(f"[ERROR] Missing data: {_missing}")
    print("Run: python examples/scripts/generate_data.py")
    sys.exit(1)

arrays = tuple(
    np.load(DATA_DIR / f"method_{m}.npy")
    for m in ("ps_ref", "deepwave", "coarse", "smooth")
)
context = DataContext(raw_data=arrays)

task = FigureTask(
    task_type="multi_method_comparison",
    title="Wavefield Comparison at $t$ = 500 ms",
    output_dir=OUT_DIR,
    method_names=(
        "(a) Pseudo-Spectral",
        "(b) Deepwave",
        "(c) Coarse ($\\Delta x$ = 20 m)",
        "(d) Smoothed",
    ),
    dx=0.01,
    dz=0.01,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Pressure (Pa)",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(7.0, 5.5),
    export_formats=("png", "pdf"),
    dpi=600,
    parameters={"cmap": "seismic"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
