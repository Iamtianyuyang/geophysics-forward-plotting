"""示例：有符号误差图（diverging colormap）。"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

ensure_example_data(DATA_DIR)

pred = np.load(DATA_DIR / "method_a.npy")
ref = np.load(DATA_DIR / "method_b.npy")
context = DataContext(raw_data=(pred, ref))

task = FigureTask(
    task_type="error_map",
    title="Signed Error Map: FD vs RTM",
    output_dir=OUT_DIR,
    dx=0.025,
    dz=0.025,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Signed Error",
    symmetric_clim=True,
    clip_percentile=99.0,
    export_formats=("png",),
    dpi=300,
    parameters={"error_mode": "signed"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("已生成文件：")
for p in result.saved_paths:
    print(f"  {p}")
