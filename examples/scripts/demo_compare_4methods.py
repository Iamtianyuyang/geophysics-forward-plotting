"""示例：四方法对比图（统一 clim，共享 colorbar，2x2 布局）。"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

ensure_example_data(DATA_DIR)

arrays = tuple(
    np.load(DATA_DIR / f"method_{c}.npy") for c in ("a", "b", "c", "d")
)
context = DataContext(raw_data=arrays)

task = FigureTask(
    task_type="multi_method_comparison",
    title="Four-Method Wavefield Comparison",
    output_dir=OUT_DIR,
    method_names=("FD", "RTM", "LSRTM", "FWI"),
    dx=0.025,
    dz=0.025,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Amplitude",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(6.0, 4.0),
    export_formats=("png", "pdf"),
    dpi=300,
    parameters={"cmap": "seismic"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("已生成文件：")
for p in result.saved_paths:
    print(f"  {p}")
