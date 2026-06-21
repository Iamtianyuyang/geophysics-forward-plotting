"""示例：性能对比柱状图（NumPy FDTD 不同网格规模运行时间）。"""

import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

with open(DATA_DIR / "perf.json", encoding="utf-8") as f:
    perf = json.load(f)

task = FigureTask(
    task_type="performance",
    title="FDTD Forward Modeling — Runtime vs Grid Size",
    output_dir=OUT_DIR,
    method_names=tuple(perf["categories"]),
    figure_size=(6.0, 4.0),
    export_formats=("png",),
    dpi=300,
    parameters={
        "values": perf["values"],
        "metric_label": perf["metric_label"],
    },
)

agent = PlottingAgent()
result = agent.run(task, DataContext())

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
