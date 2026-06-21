"""示例：有符号误差图（diverging colormap）。

比较 FD-fine 炮记录与平滑方法（模拟低频方法）的残差。
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

_REQUIRED = ["shot_record.npy", "shot_smooth.npy"]
_missing = [f for f in _REQUIRED if not (DATA_DIR / f).exists()]
if _missing:
    print(f"[ERROR] Missing data: {_missing}")
    print("Run: python examples/scripts/generate_data.py")
    sys.exit(1)

shot = np.load(DATA_DIR / "shot_record.npy")
smooth = np.load(DATA_DIR / "shot_smooth.npy")
context = DataContext(raw_data=(shot, smooth))

task = FigureTask(
    task_type="error_map",
    title="Signed Residual",
    output_dir=OUT_DIR,
    dx=0.01,
    dz=0.001,
    x_label="Offset (km)",
    y_label="Time (s)",
    colorbar_label="Residual (Pa)",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(5.5, 4.0),
    export_formats=("png",),
    dpi=600,
    parameters={"error_mode": "signed"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
