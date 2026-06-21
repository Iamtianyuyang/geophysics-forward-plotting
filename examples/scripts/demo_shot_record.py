"""示例：绘制炮记录图（deepwave 声波正演，时间向下，振幅对称色标）。"""

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
    task_type="shot_record",
    title="Synthetic Shot Record",
    output_dir=OUT_DIR,
    dt=0.001,
    dx=0.01,
    x_label="Offset (km)",
    y_label="Time (s)",
    colorbar_label="Amplitude",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(5.5, 4.0),
    export_formats=("png",),
    dpi=600,
    parameters={"cmap": "seismic"},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
