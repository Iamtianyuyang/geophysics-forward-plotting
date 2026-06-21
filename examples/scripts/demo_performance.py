"""示例：性能对比柱状图（伪谱法不同网格规模运行时间）。"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

_REQUIRED = ["perf.json"]
_missing = [f for f in _REQUIRED if not (DATA_DIR / f).exists()]
if _missing:
    print(f"[ERROR] Missing data: {_missing}")
    print("Run: python examples/scripts/generate_data.py")
    sys.exit(1)

with open(DATA_DIR / "perf.json", encoding="utf-8") as f:
    perf = json.load(f)

task = FigureTask(
    task_type="performance",
    title="Runtime vs Grid Size",
    output_dir=OUT_DIR,
    method_names=tuple(perf["categories"]),
    figure_size=(3.5, 2.6),
    export_formats=("png",),
    dpi=600,
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
