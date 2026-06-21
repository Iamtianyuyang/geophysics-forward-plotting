"""示例：绘制速度模型（五层倾斜界面 + 低速异常体）。"""

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

data = np.load(DATA_DIR / "velocity_model.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="velocity_model",
    title="Synthetic Velocity Model",
    output_dir=OUT_DIR,
    dx=0.01,
    dz=0.01,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Velocity (m/s)",
    figure_size=(8.0, 5.0),
    export_formats=("png", "pdf"),
    dpi=300,
    parameters={"cmap": "jet"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")

if result.review_messages:
    print("Review:")
    for msg in result.review_messages:
        print(f"  {msg}")
