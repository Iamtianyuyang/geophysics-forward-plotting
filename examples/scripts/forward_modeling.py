#!/usr/bin/env python3
"""
2D 声波方程正演模拟 — 伪谱法参考解 + 五层倾斜速度模型

速度模型
  Layer 0 : 0–40 行   v ≈ 1500 m/s  （水层）
  Layer 1 : 40–80 行  v ≈ 2200 m/s  （浅沉积）
  Layer 2 : 80–120 行 v ≈ 2800 m/s  （中沉积）
  Layer 3 : 120–160 行 v ≈ 3400 m/s  （深沉积）
  Layer 4 : 160+ 行    v ≈ 4000 m/s  （基底）
  + 正弦倾斜界面、低速异常体、横向梯度

无频散条件
  f0=15 Hz, v_min=1500 → λ_min=100 m, dx=10 → 10 点/波长 ✓

参数
  网格  : 200 × 400，dx = dz = 10 m
  时间  : NT=1000 步，dt=0.001 s → 仿真时长 1.0 s
  震源  : Ricker 子波，主频 15 Hz，位于模型中央上方
  方法  : 伪谱法（FFT 空间导数，谱精度）

产出 examples/data/forward/

注意：此脚本为纯 NumPy 伪谱法实现，用于无 deepwave 环境的后备。
推荐使用 generate_data.py 生成完整数据（含 deepwave 炮记录）。
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

# ─── 仿真参数 ────────────────────────────────────────────────
NZ, NX = 200, 400      # 深度 × 横向网格点数
DX     = 10.0           # 空间步长 (m)
DT     = 0.001          # 时间步长 (s)
NT     = 1000           # 时间步数
F0     = 15.0           # Ricker 子波主频 (Hz) — 降低以满足无频散条件
ABSORB = 30             # 吸收边界宽度（网格点）
REC_Z  = 2              # 接收道深度行

LAYERS = [              # (界面行号, 上层速度, 下层速度)
    (40,  1500.0, 2200.0),
    (80,  2200.0, 2800.0),
    (120, 2800.0, 3400.0),
    (160, 3400.0, 4000.0),
]

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "forward"


# ─── 工具函数 ────────────────────────────────────────────────

def make_layered_model(nz: int = NZ, nx: int = NX) -> np.ndarray:
    """构建五层倾斜速度模型。"""
    base_velocities = [1500.0, 2200.0, 2800.0, 3400.0, 4000.0]
    layer_boundaries = [40, 80, 120, 160]
    x = np.arange(nx, dtype=np.float32)

    shifted = []
    for ib in layer_boundaries:
        shift = (12 * np.sin(2 * np.pi * x / nx + ib * 0.05)).astype(int)
        shifted.append(ib + shift)

    vel = np.empty((nz, nx), dtype=np.float32)
    for ix in range(nx):
        for iz in range(nz):
            layer = sum(1 for sb in shifted if iz >= sb[ix])
            vel[iz, ix] = base_velocities[min(layer, len(base_velocities) - 1)]

    # 低速异常体
    cx, cz = nx // 4, nz // 3
    sx, sz = nx // 8, nz // 10
    zz, xx = np.ogrid[:nz, :nx]
    mask = ((zz - cz) ** 2 / sz**2 + (xx - cx) ** 2 / sx**2) < 1
    vel[mask] -= 500.0

    # 横向梯度
    vel += np.linspace(0, 200, nx, dtype=np.float32)[np.newaxis, :]
    vel = np.maximum(vel, 1400.0)

    return vel


def ricker_wavelet(f0: float, dt: float, nt: int) -> np.ndarray:
    t  = np.arange(nt, dtype=np.float64) * dt
    t0 = 1.5 / f0
    x  = np.pi * f0 * (t - t0)
    return ((1.0 - 2.0 * x**2) * np.exp(-(x**2))).astype(np.float32)


def make_sponge(nz: int, nx: int, width: int, gamma: float = 0.015) -> np.ndarray:
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
    dt: float = DT,
    nt: int = NT,
    dx: float = DX,
    absorb: int = ABSORB,
) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """伪谱法声波正演（FFT 空间导数，谱精度）。"""
    nz, nx = vel.shape
    c2 = (vel * (dt / dx)) ** 2
    sp = make_sponge(nz, nx, absorb)
    src = ricker_wavelet(f0, dt, nt)

    # 波数
    kx = np.fft.fftfreq(nx, d=dx) * 2 * np.pi
    kz = np.fft.fftfreq(nz, d=dx) * 2 * np.pi
    KX, KZ = np.meshgrid(kx, kz)
    K2 = KX**2 + KZ**2

    p     = np.zeros((nz, nx), dtype=np.float32)
    pp    = np.zeros((nz, nx), dtype=np.float32)
    record = np.zeros((nt, nx), dtype=np.float32)
    snaps: dict[int, np.ndarray] = {}

    snap_set = frozenset(snap_its)

    for it in range(nt):
        # 伪谱法 Laplacian
        P = np.fft.fft2(p)
        lap = np.real(np.fft.ifft2(-K2 * P)).astype(np.float32)

        pn               = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]
        pn               *= sp
        record[it]        = pn[REC_Z, :]

        if it in snap_set:
            snaps[it] = pn.copy()

        pp[:] = p
        p[:]  = pn

    return record, snaps


def smooth_shot(shot: np.ndarray, window: int = 15) -> np.ndarray:
    kernel = np.ones(window, dtype=np.float32) / window
    return np.apply_along_axis(
        lambda col: np.convolve(col, kernel, mode="same"),
        axis=0, arr=shot,
    ).astype(np.float32)


# ─── 主程序 ────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {OUT_DIR}\n")

    # 1. 速度模型
    print("[1/4] Building velocity model (200x400) ...")
    vel = make_layered_model()
    np.save(OUT_DIR / "velocity_model.npy", vel)
    print(f"  shape={vel.shape}  v=[{vel.min():.0f}, {vel.max():.0f}] m/s")

    # 2. FDTD 正演
    src_x, src_z = NX // 2, REC_Z
    snap_its = (200, 500, 750)

    print(f"\n[2/4] FDTD forward modeling ({NZ}x{NX} grid, {NT} steps, f0={F0} Hz) ...")
    t0 = time.perf_counter()
    shot, snaps = fdtd2d(vel, src_x, src_z, snap_its=snap_its)
    t_fdtd = time.perf_counter() - t0
    print(f"  done in {t_fdtd:.3f} s")

    np.save(OUT_DIR / "shot_record.npy", shot)
    for it, snap in snaps.items():
        t_label = int(it * DT * 1000)
        np.save(OUT_DIR / f"snap_{t_label}ms.npy", snap)

    # 3. 平滑炮记录
    print("\n[3/4] Generating smoothed shot record ...")
    shot_s = smooth_shot(shot, window=15)
    np.save(OUT_DIR / "shot_smooth.npy", shot_s)

    # 4. 不同网格规模性能基准
    print("\n[4/4] Performance benchmark (varying grid size) ...")
    cats, vals = [], []
    for nz, nx in [(100, 200), (200, 400), (300, 600)]:
        v_ = make_layered_model(nz, nx)
        t0 = time.perf_counter()
        fdtd2d(v_, nx // 2, REC_Z, snap_its=(), absorb=min(ABSORB, nz // 5))
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
    print(f"\n{'─' * 58}")
    print("All data saved:")
    for p in sorted(OUT_DIR.iterdir()):
        if p.suffix == ".npy":
            a = np.load(p)
            print(f"  {p.name:<22}  shape={str(a.shape):<14}  dtype={a.dtype}")
        else:
            print(f"  {p.name}")
    print(f"{'─' * 58}")


if __name__ == "__main__":
    main()
