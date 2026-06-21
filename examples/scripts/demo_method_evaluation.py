#!/usr/bin/env python3
"""演示 MethodEvaluationAgent：自动评估"新方法"相对基线方法的优势与缺点。

场景
  把 FDTD 炮记录当作参考解（ground truth），构造三个"方法"：
    - New Hybrid : 高精度（小噪声），但运行较慢
    - RTM        : 平滑炮记录（低频代理），精度中等
    - FD-coarse  : 大噪声、粗网格代理，精度最差但最快
  Agent 自动产出对比图 / 误差图 / 残差图 / 性能图，并给出优势-缺点结论。

前置
  python examples/scripts/forward_modeling.py   # 生成 examples/data/forward/

运行
  python examples/scripts/demo_method_evaluation.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_repo = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo / "src"))

import numpy as np

from geophysics_forward_plotting import MethodEvaluationAgent, MethodResult

DATA_DIR = _repo / "examples" / "data" / "forward"
OUT_DIR = _repo / "examples" / "outputs" / "evaluation"

DT = 0.001  # 炮记录时间步长 (s)
DX = 0.01   # 道间距 (km)


def main() -> None:
    shot = DATA_DIR / "shot_record.npy"
    smooth = DATA_DIR / "shot_smooth.npy"
    if not shot.exists() or not smooth.exists():
        print("[ERROR] 缺少正演数据，请先运行 forward_modeling.py")
        sys.exit(1)

    reference = np.load(shot).astype(np.float32)          # 当作 ground truth
    rng = np.random.default_rng(0)
    scale = float(np.abs(reference).max())

    new_method = reference + rng.normal(0, 0.01 * scale, reference.shape).astype(np.float32)
    rtm = np.load(smooth).astype(np.float32)              # 平滑 → 精度中等
    fd_coarse = reference + rng.normal(0, 0.05 * scale, reference.shape).astype(np.float32)

    agent = MethodEvaluationAgent()
    report = agent.evaluate(
        new_method=MethodResult("New Hybrid", new_method, runtime=14.2),
        baselines=[
            MethodResult("RTM", rtm, runtime=8.1),
            MethodResult("FD-coarse", fd_coarse, runtime=3.4),
        ],
        reference=reference,
        figure_kind="shot_record",
        output_dir=OUT_DIR,
        colorbar_label="Amplitude",
        dx=DX, dt=DT,
        dpi=300,
    )

    print(report.render_text())


if __name__ == "__main__":
    main()
