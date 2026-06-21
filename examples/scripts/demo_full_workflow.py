#!/usr/bin/env python3
"""
完整工作流演示：五层速度模型 → PlottingAgent → 7 种 Skill 绘图

数据来源
  python examples/scripts/generate_data.py   # 生成 deepwave + 伪谱法数据

运行
  cd geophysics-forward-plotting
  python examples/scripts/demo_full_workflow.py

产出 examples/outputs/forward/*.png（7 张论文级图件）
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_repo = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo / "src"))

import numpy as np  # noqa: E402

from geophysics_forward_plotting import PlottingAgent  # noqa: E402
from geophysics_forward_plotting.core.models import DataContext, FigureTask  # noqa: E402

DATA_DIR = _repo / "examples" / "data"
OUT_DIR  = _repo / "examples" / "outputs" / "forward"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 仿真参数（与 generate_data.py 一致）
DX = 0.01   # 空间步长 km（10 m = 0.01 km）
DT = 0.001  # 时间步长 s

agent = PlottingAgent()


def _check_data() -> None:
    required = ["velocity_model.npy", "shot_record.npy", "shot_smooth.npy",
                "snap_200ms.npy", "snap_500ms.npy", "snap_750ms.npy", "perf.json"]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        print(f"[ERROR] Missing data files: {missing}")
        print("Run: python examples/scripts/generate_data.py")
        sys.exit(1)


def banner(msg: str) -> None:
    print(f"\n{'-' * 58}")
    print(f"  {msg}")
    print(f"{'-' * 58}")


def show(result) -> None:
    for p in result.saved_paths:
        print(f"  [OK] {p.relative_to(_repo)}")
    for m in result.review_messages:
        prefix = "  [WARN]" if "WARNING" in m else "  [INFO]"
        print(f"{prefix} {m}")


# ================================================================
_check_data()

# ────────────────────────────────────────────────────────────────
# 1. 速度模型
# ────────────────────────────────────────────────────────────────
banner("1 / 7  VelocityModelSkill")

vel = np.load(DATA_DIR / "velocity_model.npy")
show(agent.run(
    FigureTask(
        task_type      = "velocity_model",
        output_dir     = OUT_DIR,
        title          = "Synthetic Velocity Model",
        x_label        = "Distance (km)",
        y_label        = "Depth (km)",
        colorbar_label = "Velocity (m s$^{-1}$)",
        dx=DX, dz=DX,
        figure_size    = (3.5, 2.8),
        dpi=600, export_formats=("png",),
        parameters     = {"cmap": "jet"},
    ),
    DataContext(raw_data=(vel,)),
))


# ────────────────────────────────────────────────────────────────
# 2. 炮记录
# ────────────────────────────────────────────────────────────────
banner("2 / 7  ShotRecordSkill")

shot = np.load(DATA_DIR / "shot_record.npy")
show(agent.run(
    FigureTask(
        task_type      = "shot_record",
        output_dir     = OUT_DIR,
        title          = "Shot Record (src at x = 2.0 km)",
        x_label        = "Distance (km)",
        y_label        = "Time (s)",
        colorbar_label = "Amplitude",
        dx=DX, dt=DT,
        figure_size    = (5.5, 4.0),
        dpi=600, export_formats=("png",),
    ),
    DataContext(raw_data=(shot,)),
))


# ────────────────────────────────────────────────────────────────
# 3. 波场快照
# ────────────────────────────────────────────────────────────────
banner("3 / 7  WavefieldSnapshotSkill (t=500 ms)")

snap = np.load(DATA_DIR / "snap_500ms.npy")
show(agent.run(
    FigureTask(
        task_type      = "wavefield_snapshot",
        output_dir     = OUT_DIR,
        title          = "Acoustic Wavefield",
        x_label        = "Distance (km)",
        y_label        = "Depth (km)",
        colorbar_label = "Amplitude",
        dx=DX, dz=DX,
        figure_size    = (3.5, 2.8),
        dpi=600, export_formats=("png",),
        parameters     = {"snapshot_time": 0.5},
    ),
    DataContext(raw_data=(snap,)),
))


# ────────────────────────────────────────────────────────────────
# 4. 多时刻波场对比
# ────────────────────────────────────────────────────────────────
banner("4 / 7  MultiMethodCompareSkill (3 snapshots)")

s200 = np.load(DATA_DIR / "snap_200ms.npy")
s500 = np.load(DATA_DIR / "snap_500ms.npy")
s750 = np.load(DATA_DIR / "snap_750ms.npy")
show(agent.run(
    FigureTask(
        task_type      = "multi_method_comparison",
        output_dir     = OUT_DIR,
        title          = "Wavefield Propagation — 3 Time Snapshots",
        x_label        = "Distance (km)",
        y_label        = "Depth (km)",
        colorbar_label = "Amplitude",
        method_names   = ("t = 200 ms", "t = 500 ms", "t = 750 ms"),
        symmetric_clim = True,
        dx=DX, dz=DX,
        figure_size    = (12.0, 4.0),
        dpi=600, export_formats=("png",),
    ),
    DataContext(raw_data=(s200, s500, s750)),
))


# ────────────────────────────────────────────────────────────────
# 5. Wiggle 图
# ────────────────────────────────────────────────────────────────
banner("5 / 7  WiggleSkill")

show(agent.run(
    FigureTask(
        task_type   = "wiggle",
        output_dir  = OUT_DIR,
        title       = "Wiggle Display",
        x_label     = "Distance (km)",
        y_label     = "Time (s)",
        dx=DX, dt=DT,
        figure_size = (5.5, 4.0),
        dpi=600, export_formats=("png",),
        parameters  = {"skip": 10, "gain": 2.0, "fill_positive": True},
    ),
    DataContext(raw_data=(shot,)),
))


# ────────────────────────────────────────────────────────────────
# 6. 误差图
# ────────────────────────────────────────────────────────────────
banner("6 / 7  ErrorMapSkill (FD-fine vs Smoothed)")

shot_s = np.load(DATA_DIR / "shot_smooth.npy")
show(agent.run(
    FigureTask(
        task_type      = "error_map",
        output_dir     = OUT_DIR,
        title          = "Signed Residual: FD-fine vs Smoothed",
        x_label        = "Distance (km)",
        y_label        = "Time (s)",
        colorbar_label = "Signed Residual",
        dx=DX,
        dz=DT,
        figure_size    = (8.0, 6.0),
        dpi=300, export_formats=("png",),
        parameters     = {"error_mode": "signed"},
    ),
    DataContext(raw_data=(shot, shot_s)),
))


# ────────────────────────────────────────────────────────────────
# 7. 性能对比
# ────────────────────────────────────────────────────────────────
banner("7 / 7  PerformanceSkill")

with open(DATA_DIR / "perf.json", encoding="utf-8") as f:
    perf = json.load(f)

show(agent.run(
    FigureTask(
        task_type    = "performance",
        output_dir   = OUT_DIR,
        title        = "FDTD Forward Modeling — Runtime vs Grid Size",
        method_names = tuple(perf["categories"]),
        dpi=300, export_formats=("png",),
        parameters   = {
            "values"       : perf["values"],
            "metric_label" : perf["metric_label"],
        },
    ),
))


# ================================================================
print(f"\n{'=' * 58}")
print(f"  All 7 figures saved to: {OUT_DIR.relative_to(_repo)}")
print(f"{'=' * 58}")
for f in sorted(OUT_DIR.glob("*.png")):
    sz = f.stat().st_size // 1024
    print(f"  {f.name:<40} {sz:>5} KB")
