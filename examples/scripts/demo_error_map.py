"""示例：有符号误差图（diverging colormap）。

比较 FD-fine 炮记录与平滑方法（模拟低频方法）的残差。
"""

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

shot = np.load(DATA_DIR / "shot_record.npy")
smooth = np.load(DATA_DIR / "shot_smooth.npy")
context = DataContext(raw_data=(shot, smooth))

task = FigureTask(
    task_type="error_map",
    title="Signed Residual: FD-fine vs Smoothed",
    output_dir=OUT_DIR,
    dx=0.01,
    dz=0.001,
    x_label="Distance (km)",
    y_label="Time (s)",
    colorbar_label="Signed Residual",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(8.0, 6.0),
    export_formats=("png",),
    dpi=300,
    parameters={"error_mode": "signed"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
