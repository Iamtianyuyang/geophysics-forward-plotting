#!/usr/bin/env python3
"""
2D 声波方程正演模拟 — 层状速度模型（纯 NumPy，无额外依赖）

层状模型
  Layer 1 :  0 – 300 m   v = 1500 m/s  （水层）
  Layer 2 : 300 – 700 m  v = 2500 m/s  （沉积层）
  Layer 3 : 700 m+        v = 3500 m/s  （基底）

参数
  网格  : 100 × 200，dx = dz = 10 m
  时间  : NT=800 步，dt=0.001 s → 仿真时长 0.8 s
  震源  : Ricker 子波，主频 25 Hz，位于模型中央上方
  接收  : 全孔径地表 200 道

产出 examples/data/forward/
  velocity_model.npy   (100, 200)  速度模型
  shot_record.npy      (800, 200)  FDTD 炮记录
  shot_smooth.npy      (800, 200)  时间方向平滑炮记录（模拟低频方法）
  snap_200ms.npy       (100, 200)  t = 200 ms 波场快照
  snap_500ms.npy       (100, 200)  t = 500 ms 波场快照
  snap_750ms.npy       (100, 200)  t = 750 ms 波场快照
  perf.json                        不同网格规模运行时间

运行
  cd geophysics-forward-plotting
  python examples/scripts/forward_modeling.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

# ─── 仿真参数 ────────────────────────────────────────────────
NZ, NX = 100, 200    # 深度 × 横向网格点数
DX     = 10.0        # 空间步长 (m)；dx = dz = DX
DT     = 0.001       # 时间步长 (s)；CFL = 3500*0.001/10 = 0.35 < 0.707 ✓
NT     = 800         # 时间步数
F0     = 25.0        # Ricker 子波主频 (Hz)
ABSORB = 20          # 吸收边界宽度（网格点）
REC_Z  = 1           # 接收道深度行（row 0 是 Dirichlet 零边界，恒为 0）

LAYERS = [           # (起始行索引, 速度 m/s)
    (0,  1500.0),
    (30, 2500.0),
    (70, 3500.0),
]

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "forward"


# ─── 工具函数 ────────────────────────────────────────────────

def make_layered_model(nz: int = NZ, nx: int = NX) -> np.ndarray:
    """构建层状速度模型。"""
    vel = np.full((nz, nx), LAYERS[0][1], dtype=np.float32)
    for iz, v in LAYERS[1:]:
        if iz < nz:
            vel[iz:] = v
    return vel


def ricker_wavelet(f0: float, dt: float, nt: int) -> np.ndarray:
    """Ricker 子波（墨西哥帽小波）。"""
    t  = np.arange(nt, dtype=np.float64) * dt
    t0 = 1.5 / f0
    x  = np.pi * f0 * (t - t0)
    return ((1.0 - 2.0 * x**2) * np.exp(-(x**2))).astype(np.float32)


def make_sponge(nz: int, nx: int, width: int, gamma: float = 0.015) -> np.ndarray:
    """
    Cerjan-style 海绵吸收边界。
    gamma=0.015, width=20 ≈ 99% 吸收（波穿越吸收区来回）。
    """
    s = np.ones((nz, nx), dtype=np.float32)
    for i in range(width):
        val = float(np.exp(-((gamma * (width - i)) ** 2)))
        s[i,       :] *= val
        s[-(i + 1), :] *= val
        s[:,        i] *= val
        s[:, -(i + 1)] *= val
    return s


def fdtd2d(
    vel: np.ndarray,
    src_x: int,
    src_z: int,
    snap_its: tuple[int, ...] = (),
    f0: float = F0,
    absorb: int = ABSORB,
) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """
    2 阶时间 / 2 阶空间 有限差分正演。

    参数
    ----
    vel      : (nz, nx) 速度模型 (m/s)
    src_x/z  : 震源网格坐标
    snap_its : 保存波场快照的时间步集合
    f0       : Ricker 子波主频 (Hz)
    absorb   : 吸收边界宽度（网格点）

    返回
    ----
    record : (NT, nx) float32  地表炮记录
    snaps  : {it: (nz, nx) float32} 波场快照字典
    """
    nz, nx = vel.shape

    # (c·Δt/Δx)² — 稳定性要求 < 1/√2 ≈ 0.707
    c2 = (vel * (DT / DX)) ** 2

    sp    = make_sponge(nz, nx, absorb)
    src   = ricker_wavelet(f0, DT, NT)

    p     = np.zeros((nz, nx), dtype=np.float32)
    pp    = np.zeros((nz, nx), dtype=np.float32)
    record = np.zeros((NT, nx), dtype=np.float32)
    snaps: dict[int, np.ndarray] = {}

    snap_set = frozenset(snap_its)

    for it in range(NT):
        # 二阶空间 Laplacian（仅内部节点）
        lap = np.zeros_like(p)
        lap[1:-1, 1:-1] = (
            p[2:,   1:-1] + p[:-2,  1:-1]
          + p[1:-1, 2:  ] + p[1:-1, :-2 ]
          - 4.0 * p[1:-1, 1:-1]
        )

        pn               = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]   # 点源注入（爆炸点源）
        pn               *= sp         # 吸收边界衰减
        record[it]        = pn[REC_Z, :]   # 近地表接收道（row 0 是固定零边界，不能用）

        if it in snap_set:
            snaps[it] = pn.copy()

        pp[:] = p
        p[:]  = pn

    return record, snaps


def smooth_shot(shot: np.ndarray, window: int = 11) -> np.ndarray:
    """
    时间方向滑动平均，模拟低频/粗网格方法的炮记录。
    用于构造误差图的"对比方法"数据。
    """
    kernel = np.ones(window, dtype=np.float32) / window
    return np.apply_along_axis(
        lambda col: np.convolve(col.astype(np.float32), kernel, mode="same"),
        axis=0,
        arr=shot,
    ).astype(np.float32)


# ─── 主程序 ────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {OUT_DIR}\n")

    # 1. 速度模型
    print("[1/4] Building layered velocity model ...")
    vel = make_layered_model()
    np.save(OUT_DIR / "velocity_model.npy", vel)
    print(f"  shape={vel.shape}  v=[{vel.min():.0f}, {vel.max():.0f}] m/s")

    # 2. FDTD 正演
    src_x, src_z = NX // 2, 2          # 震源：中央，近地表
    snap_its     = (200, 500, 750)      # 保存快照的时间步

    print(f"\n[2/4] FDTD forward modeling  ({NZ}x{NX} grid, {NT} steps, f0={F0} Hz) ...")
    t0 = time.perf_counter()
    shot, snaps = fdtd2d(vel, src_x, src_z, snap_its=snap_its)
    t_fdtd = time.perf_counter() - t0
    print(f"  done in {t_fdtd:.3f} s")

    np.save(OUT_DIR / "shot_record.npy", shot)
    np.save(OUT_DIR / "snap_200ms.npy",  snaps[200])
    np.save(OUT_DIR / "snap_500ms.npy",  snaps[500])
    np.save(OUT_DIR / "snap_750ms.npy",  snaps[750])

    # 3. 平滑对比数据
    print("\n[3/4] Generating smoothed shot record (low-freq method proxy) ...")
    t0     = time.perf_counter()
    shot_s = smooth_shot(shot, window=11)
    t_s    = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_smooth.npy", shot_s)
    print(f"  done in {t_s*1000:.1f} ms")

    # 4. 不同网格规模性能基准
    print("\n[4/4] Performance benchmark (varying grid size) ...")
    cats, vals = [], []
    for nz, nx in [(50, 100), (100, 200), (150, 300)]:
        v_ = make_layered_model(nz, nx)
        t0 = time.perf_counter()
        fdtd2d(v_, nx // 2, 2, absorb=min(ABSORB, nz // 5))
        elapsed = round(time.perf_counter() - t0, 3)
        cats.append(f"{nz}x{nx}")
        vals.append(elapsed)
        print(f"  grid {nz}x{nx}  -> {elapsed:.3f} s")

    with open(OUT_DIR / "perf.json", "w", encoding="utf-8") as f:
        json.dump(
            {"categories": cats, "values": vals, "metric_label": "Runtime (s)"},
            f, indent=2,
        )

    # 汇总
    print(f"\n{'─' * 54}")
    print("All data saved:")
    for p in sorted(OUT_DIR.iterdir()):
        if p.suffix == ".npy":
            a = np.load(p)
            print(f"  {p.name:<22}  shape={str(a.shape):<12}  dtype={a.dtype}")
        else:
            print(f"  {p.name}")
    print(f"{'─' * 54}")


if __name__ == "__main__":
    main()
