"""示例：绘制波场快照（深度向下，振幅对称，标注快照时刻）。"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

ensure_example_data(DATA_DIR)

data = np.load(DATA_DIR / "wavefield_snapshot.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="wavefield_snapshot",
    title="Wavefield Snapshot at t=0.30 s",
    output_dir=OUT_DIR,
    dx=0.025,
    dz=0.025,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Amplitude",
    symmetric_clim=True,
    clip_percentile=99.0,
    export_formats=("png",),
    dpi=300,
    parameters={"cmap": "seismic", "snapshot_time": 0.30},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("已生成文件：")
for p in result.saved_paths:
    print(f"  {p}")
