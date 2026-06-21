"""示例：3D 地震体可视化（需要 cigvis + vispy + GUI 环境）。"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.backend.cigvis_backend import is_available
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

ensure_example_data(DATA_DIR)

if not is_available():
    print("cigvis 未安装，无法运行 3D volume 示例。")
    print("请安装：pip install cigvis")
    raise SystemExit(0)

data = np.load(DATA_DIR / "volume_3d.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="volume_3d",
    title="3D Seismic Volume",
    output_dir=OUT_DIR,
    symmetric_clim=True,
    clip_percentile=99.0,
    parameters={"cmap": "gray", "slices": [15, 15, 30]},
)

agent = PlottingAgent()
result = agent.run(task, context)
print(result.summary)
