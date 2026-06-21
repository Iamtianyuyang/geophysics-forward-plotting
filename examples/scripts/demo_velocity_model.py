"""示例：绘制速度模型。

运行方式
--------
conda activate geophysics-forward-plotting
python examples/scripts/demo_velocity_model.py
"""

from pathlib import Path

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext
from geophysics_forward_plotting.utils.sample_data import ensure_example_data

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

# 生成示例数据（若不存在）
ensure_example_data(DATA_DIR)

# 加载数据
data = np.load(DATA_DIR / "velocity_model.npy")
context = DataContext(raw_data=(data,))

# 构建任务
task = FigureTask(
    task_type="velocity_model",
    title="Marmousi-like Velocity Model",
    output_dir=OUT_DIR,
    dx=0.025,
    dz=0.025,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Velocity (m/s)",
    export_formats=("png", "pdf"),
    dpi=300,  # 示例用 300 dpi，论文用 600
    parameters={"cmap": "jet"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("已生成文件：")
for p in result.saved_paths:
    print(f"  {p}")

if result.review_messages:
    print("规范检查：")
    for msg in result.review_messages:
        print(f"  {msg}")
