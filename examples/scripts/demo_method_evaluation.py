#!/usr/bin/env python3
"""演示 MethodEvaluationAgent：评估不同方法相对于参考解的表现。

场景
  使用 deepwave + FDTD 生成的正演数据作为参考解（ground truth），构造三个方法：
    - FD-fine    : 精细网格 FDTD（参考解本身）
    - FD-coarse  : 粗网格 FDTD（分辨率降低，精度中等）
    - Smoothed   : 高斯低通滤波（模拟低频方法，精度最差）
  Agent 自动产出对比图 / 误差图 / 残差图 / 性能图，并给出优势-缺点结论。

前置
  python examples/scripts/generate_data.py

运行
  python examples/scripts/demo_method_evaluation.py
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_repo = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo / "src"))

import numpy as np

from geophysics_forward_plotting import MethodEvaluationAgent, MethodResult

DATA_DIR = _repo / "examples" / "data"
OUT_DIR = _repo / "examples" / "outputs" / "evaluation"

DT = 0.001
DX = 0.01


def main() -> None:
    required = ["method_ps_ref.npy", "method_deepwave.npy",
                "method_smooth.npy", "method_coarse.npy", "perf.json"]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        print(f"[ERROR] Missing data: {missing}")
        print("Run: python examples/scripts/generate_data.py")
        sys.exit(1)

    reference = np.load(DATA_DIR / "method_ps_ref.npy").astype(np.float32)
    deepwave  = np.load(DATA_DIR / "method_deepwave.npy").astype(np.float32)
    smoothed  = np.load(DATA_DIR / "method_smooth.npy").astype(np.float32)
    coarse    = np.load(DATA_DIR / "method_coarse.npy").astype(np.float32)

    with open(DATA_DIR / "perf.json", encoding="utf-8") as f:
        perf = json.load(f)
    runtime_ref = perf["values"][1]    # 200x400 ~ standard grid

    agent = MethodEvaluationAgent()
    report = agent.evaluate(
        new_method=MethodResult("Deepwave", deepwave, runtime=runtime_ref),
        baselines=[
            MethodResult("Coarse (dx=20m)", coarse, runtime=perf["values"][0]),
            MethodResult("Smoothed", smoothed, runtime=runtime_ref * 0.5),
        ],
        reference=reference,
        figure_kind="wavefield_snapshot",
        output_dir=OUT_DIR,
        colorbar_label="Amplitude",
        dx=DX, dz=DX,
        dpi=300,
    )

    print(report.render_text())


if __name__ == "__main__":
    main()
