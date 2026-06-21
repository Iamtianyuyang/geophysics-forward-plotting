"""示例：性能对比柱状图（计算时间）。"""

from pathlib import Path

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

OUT_DIR = Path("examples/outputs")

task = FigureTask(
    task_type="performance",
    title="Computational Time Comparison",
    output_dir=OUT_DIR,
    method_names=("FD", "RTM", "LSRTM", "FWI"),
    figure_size=(6.0, 4.0),
    export_formats=("png",),
    dpi=300,
    parameters={
        "categories": ["FD", "RTM", "LSRTM", "FWI"],
        "values": [1.2, 4.5, 9.8, 38.6],
        "metric_label": "Time (s)",
        "chart_type": "bar",
    },
)

agent = PlottingAgent()
result = agent.run(task, DataContext())

print("已生成文件：")
for p in result.saved_paths:
    print(f"  {p}")
