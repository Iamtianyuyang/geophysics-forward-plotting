"""示例：地震道 wiggle 图（deepwave 炮记录，时间向下，正值填充）。"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

_REQUIRED = ["shot_record.npy"]
_missing = [f for f in _REQUIRED if not (DATA_DIR / f).exists()]
if _missing:
    print(f"[ERROR] Missing data: {_missing}")
    print("Run: python examples/scripts/generate_data.py")
    sys.exit(1)

data = np.load(DATA_DIR / "shot_record.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="wiggle",
    title="Seismic Wiggle Display",
    output_dir=OUT_DIR,
    dt=0.001,
    dx=0.01,
    x_label="Offset (km)",
    y_label="Time (s)",
    figure_size=(5.5, 4.0),
    export_formats=("png",),
    dpi=600,
    parameters={"skip": 10, "gain": 2.0, "fill_positive": True},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
