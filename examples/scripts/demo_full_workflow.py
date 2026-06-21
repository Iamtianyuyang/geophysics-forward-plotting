#!/usr/bin/env python3
"""
完整工作流演示：层状模型正演数据 → PlottingAgent → 7 种 Skill 绘图

前置
  python examples/scripts/forward_modeling.py   # 生成正演数据

运行
  cd geophysics-forward-plotting
  python examples/scripts/demo_full_workflow.py

产出 examples/outputs/forward/*.png（7 张论文级图件）
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")   # 无显示器环境下渲染

_repo = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo / "src"))

import numpy as np

from geophysics_forward_plotting import PlottingAgent
from geophysics_forward_plotting.core.models import DataContext, FigureTask

DATA_DIR = _repo / "examples" / "data" / "forward"
OUT_DIR  = _repo / "examples" / "outputs" / "forward"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 仿真参数（与 forward_modeling.py 一致）
DX = 0.01   # 空间步长 km（10 m = 0.01 km）
DT = 0.001  # 时间步长 s

agent = PlottingAgent()          # 默认注册全部 13 个内置 Skill


def _check_data() -> None:
    required = ["velocity_model.npy", "shot_record.npy", "shot_smooth.npy",
                "snap_200ms.npy", "snap_500ms.npy", "snap_750ms.npy", "perf.json"]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        print(f"[ERROR] 缺少数据文件: {missing}")
        print("请先运行：python examples/scripts/forward_modeling.py")
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


# ═══════════════════════════════════════════════════════════
_check_data()

# ───────────────────────────────────────────────────────────
# 1. 速度模型  ── VelocityModelSkill
# ───────────────────────────────────────────────────────────
banner("1 / 7  VelocityModelSkill — 速度模型")
# 约定：非对称色标（速度单调），cmap=jet，深度轴向下

vel = np.load(DATA_DIR / "velocity_model.npy")
show(agent.run(
    FigureTask(
        task_type      = "velocity_model",
        output_dir     = OUT_DIR,
        title          = "Layered Velocity Model",
        x_label        = "Distance (km)",
        y_label        = "Depth (km)",
        colorbar_label = "Velocity (m/s)",
        dx=DX, dz=DX,
        dpi=300, export_formats=("png",),
        parameters     = {"cmap": "jet"},
    ),
    DataContext(raw_data=(vel,)),
))


# ───────────────────────────────────────────────────────────
# 2. 炮记录  ── ShotRecordSkill
# ───────────────────────────────────────────────────────────
banner("2 / 7  ShotRecordSkill — 炮记录（震源居中）")
# 约定：强制对称色标，diverging cmap (seismic)，时间轴向下

shot = np.load(DATA_DIR / "shot_record.npy")
show(agent.run(
    FigureTask(
        task_type      = "shot_record",
        output_dir     = OUT_DIR,
        title          = "Shot Record  (src at x = 1.0 km)",
        x_label        = "Distance (km)",
        y_label        = "Time (s)",
        colorbar_label = "Amplitude",
        dx=DX, dt=DT,
        dpi=300, export_formats=("png",),
    ),
    DataContext(raw_data=(shot,)),
))


# ───────────────────────────────────────────────────────────
# 3. 波场快照  ── WavefieldSnapshotSkill
# ───────────────────────────────────────────────────────────
banner("3 / 7  WavefieldSnapshotSkill — 波场快照 t=500 ms")
# 约定：对称色标，时刻标注在图上，深度轴向下

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
        dpi=300, export_formats=("png",),
        parameters     = {"snapshot_time": 0.5},   # 图上标注 t=0.5 s
    ),
    DataContext(raw_data=(snap,)),
))


# ───────────────────────────────────────────────────────────
# 4. 多时刻波场对比  ── MultiMethodCompareSkill
# ───────────────────────────────────────────────────────────
banner("4 / 7  MultiMethodCompareSkill — 三时刻波场对比（统一 clim）")
# 约定：全局统一 clim，共享 colorbar，≤2 个 → 1×N，3~4 个 → 2×2

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
        symmetric_clim = True,   # 跨所有 panel 统一色标范围
        dx=DX, dz=DX,
        dpi=300, export_formats=("png",),
    ),
    DataContext(raw_data=(s200, s500, s750)),
))


# ───────────────────────────────────────────────────────────
# 5. Wiggle 图  ── WiggleSkill
# ───────────────────────────────────────────────────────────
banner("5 / 7  WiggleSkill — 变面积 Wiggle 炮记录")
# 约定：时间轴向下，正振幅填黑，skip 控制道稀疏程度

show(agent.run(
    FigureTask(
        task_type   = "wiggle",
        output_dir  = OUT_DIR,
        title       = "Shot Record (Wiggle Display, every 8th trace)",
        x_label     = "Distance (km)",
        y_label     = "Time (s)",
        dx=DX, dt=DT,
        figure_size = (10.0, 6.0),
        dpi=300, export_formats=("png",),
        parameters  = {
            "skip"         : 8,     # 每 8 道显示 1 道 → 25 道
            "gain"         : 2.0,   # 振幅放大系数
            "fill_positive": True,  # 正振幅区域填黑
        },
    ),
    DataContext(raw_data=(shot,)),
))


# ───────────────────────────────────────────────────────────
# 6. 误差图  ── ErrorMapSkill
# ───────────────────────────────────────────────────────────
banner("6 / 7  ErrorMapSkill — FDTD 炮记录 vs 平滑方法 残差图")
# 约定：signed → diverging cmap；absolute → sequential cmap
# raw_data = (预测值, 参考值)；dz 用时间步长代替深度步长

shot_s = np.load(DATA_DIR / "shot_smooth.npy")
show(agent.run(
    FigureTask(
        task_type      = "error_map",
        output_dir     = OUT_DIR,
        title          = "Residual: FDTD − Smooth",
        x_label        = "Distance (km)",
        y_label        = "Time (s)",
        colorbar_label = "Signed Residual",
        dx=DX,
        dz=DT,          # ← 此处 dz 代表时间步长（炮记录纵轴为时间）
        dpi=300, export_formats=("png",),
        parameters     = {"error_mode": "signed"},
    ),
    DataContext(raw_data=(shot, shot_s)),   # (预测值, 参考值)
))


# ───────────────────────────────────────────────────────────
# 7. 性能对比  ── PerformanceSkill
# ───────────────────────────────────────────────────────────
banner("7 / 7  PerformanceSkill — 不同网格规模运行时间对比")
# 约定：数据来自 task.parameters（不需要 .npy 文件）

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


# ═══════════════════════════════════════════════════════════
print(f"\n{'=' * 58}")
print(f"  All 7 figures saved to: {OUT_DIR.relative_to(_repo)}")
print(f"{'=' * 58}")
for f in sorted(OUT_DIR.glob("*.png")):
    sz = f.stat().st_size // 1024
    print(f"  {f.name:<40} {sz:>5} KB")
