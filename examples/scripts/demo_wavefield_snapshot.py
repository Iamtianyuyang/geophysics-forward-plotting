"""示例：绘制波场快照（deepwave 声波正演，深度向下，振幅对称，标注快照时刻）。"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

DATA_DIR = Path("examples/data")
OUT_DIR = Path("examples/outputs")

_REQUIRED = ["snap_500ms.npy"]
_missing = [f for f in _REQUIRED if not (DATA_DIR / f).exists()]
if _missing:
    print(f"[ERROR] Missing data: {_missing}")
    print("Run: python examples/scripts/generate_data.py")
    sys.exit(1)

data = np.load(DATA_DIR / "snap_500ms.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="wavefield_snapshot",
    title="Acoustic Wavefield",
    output_dir=OUT_DIR,
    dx=0.01,
    dz=0.01,
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Pressure (Pa)",
    symmetric_clim=True,
    clip_percentile=99.0,
    figure_size=(3.5, 2.8),
    export_formats=("png",),
    dpi=600,
    parameters={"cmap": "seismic", "snapshot_time": 0.5},
)

agent = PlottingAgent()
result = agent.run(task, context)

print("Generated files:")
for p in result.saved_paths:
    print(f"  {p}")
