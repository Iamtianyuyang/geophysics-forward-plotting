"""示例：绘制炮记录图（时间向下，振幅对称色标）。"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

ensure_example_data(DATA_DIR)

data = np.load(DATA_DIR / "shot_record.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="shot_record",
    title="Synthetic Shot Record",
    output_dir=OUT_DIR,
    dt=0.002,
    dx=0.025,
    x_label="Receiver position (km)",
    y_label="Time (s)",
    colorbar_label="Amplitude",
    symmetric_clim=True,
    clip_percentile=99.0,
    export_formats=("png",),
    dpi=300,
    parameters={"cmap": "seismic"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("已生成文件：")
for p in result.saved_paths:
    print(f"  {p}")
