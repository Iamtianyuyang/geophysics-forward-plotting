"""示例：cigvis SliceViewer 交互式 3D 切片浏览（需要 cigvis + GUI 环境）。"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.backend.cigvis_backend import is_available
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")

ensure_example_data(DATA_DIR)

if not is_available():
    print("cigvis 未安装，无法运行 SliceViewer 示例。")
    print("请安装：pip install cigvis")
    raise SystemExit(0)

data = np.load(DATA_DIR / "volume_3d.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="sliceviewer",
    title="Interactive SliceViewer",
    symmetric_clim=False,
    clip_percentile=99.0,
    parameters={"cmap": "gray"},
)

agent = PlottingAgent()
result = agent.run(task, context)
print(result.summary)
