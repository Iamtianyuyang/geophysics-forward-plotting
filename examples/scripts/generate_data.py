#!/usr/bin/env python3
"""
用 deepwave scalar()（官方推荐 API）+ 伪谱法生成全套示例数据。

参考: https://ausargeo.com/deepwave/example_forward_model

无频散条件
  f0=15 Hz, v_min=1500 m/s → λ_min=100 m, dx=10 m → 10 点/波长 ✓

关键参数（与官方示例一致）
  - scalar() 函数（非 Acoustic 类）
  - accuracy=8（8 阶空间有限差分）
  - pml_freq=f0（PML 优化频率）

运行
  cd geophysics-forward-plotting
  python examples/scripts/generate_data.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

OUT_DIR = REPO / "examples" / "data"

# ─── 仿真参数 ────────────────────────────────────────────────
NZ, NX   = 200, 400
DX       = 10.0        # m
DT       = 0.001       # s
NT       = 1000        # 1.0 s
F0       = 15.0        # Hz
ABSORB   = 30
REC_DEPTH = 2          # 接收器深度行索引


# ─── 速度模型 ────────────────────────────────────────────────

def make_velocity_model(
    nz: int = NZ, nx: int = NX, dx: float = DX,
) -> NDArray:
    """
    五层倾斜速度模型：
      Layer 0 : 0–40 行   v ≈ 1500 m/s
      Layer 1 : 40–80 行  v ≈ 2200 m/s
      Layer 2 : 80–120 行 v ≈ 2800 m/s
      Layer 3 : 120–160 行 v ≈ 3400 m/s
      Layer 4 : 160+ 行    v ≈ 4000 m/s
    含正弦倾斜界面、高斯低速异常体、横向梯度。
    """
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

    cx, cz = nx // 4, nz // 3
    sx, sz = nx // 8, nz // 10
    zz, xx = np.ogrid[:nz, :nx]
    mask = ((zz - cz) ** 2 / sz**2 + (xx - cx) ** 2 / sx**2) < 1
    vel[mask] -= 500.0

    vel += np.linspace(0, 200, nx, dtype=np.float32)[np.newaxis, :]
    vel = np.maximum(vel, 1400.0)
    return vel


# ─── Ricker 子波 ─────────────────────────────────────────────

def ricker(f0: float, dt: float, nt: int) -> NDArray:
    t = np.arange(nt, dtype=np.float64) * dt
    t0 = 1.5 / f0
    x = np.pi * f0 * (t - t0)
    return ((1.0 - 2.0 * x**2) * np.exp(-(x**2))).astype(np.float32)


# ─── deepwave scalar() 正演 ─────────────────────────────────

def deepwave_shot_record(
    vel: NDArray,
    src_x: int,
    src_depth: int = REC_DEPTH,
    dx: float = DX,
    dt: float = DT,
    nt: int = NT,
    f0: float = F0,
) -> NDArray:
    """用 deepwave scalar() 生成炮记录 (nt, nx)。"""
    import torch
    import deepwave

    nz, nx = vel.shape
    v = torch.from_numpy(vel.copy())

    # 震源: (n_shots=1, n_src=1, dim=2) — [dim0_idx, dim1_idx]
    source_locations = torch.zeros(1, 1, 2, dtype=torch.long)
    source_locations[0, 0, 0] = src_depth   # dim0 = depth
    source_locations[0, 0, 1] = src_x       # dim1 = horizontal

    # 接收器: (n_shots=1, n_rec=nx, dim=2)
    receiver_locations = torch.zeros(1, nx, 2, dtype=torch.long)
    receiver_locations[0, :, 0] = REC_DEPTH
    receiver_locations[0, :, 1] = torch.arange(nx)

    # 震源子波: (n_shots=1, n_src=1, nt)
    source_amplitudes = (
        deepwave.wavelets.ricker(f0, nt, dt, 1.5 / f0)
        .reshape(1, 1, -1)
    )

    out = deepwave.scalar(
        v, dx, dt,
        source_amplitudes=source_amplitudes,
        source_locations=source_locations,
        receiver_locations=receiver_locations,
        accuracy=8,
        pml_freq=f0,
    )

    # 炮记录 = out[-1]: (n_shots=1, n_rec, nt) → (nt, n_rec)
    shot = out[-1][0].cpu().T.numpy().astype(np.float32)
    return shot


def deepwave_snapshots(
    vel: NDArray,
    src_x: int,
    snap_its: tuple[int, ...],
    src_depth: int = REC_DEPTH,
    dx: float = DX,
    dt: float = DT,
    nt: int = NT,
    f0: float = F0,
) -> dict[int, NDArray]:
    """用 deepwave scalar() + forward_callback 获取波场快照。"""
    import torch
    import deepwave

    nz, nx = vel.shape
    v = torch.from_numpy(vel.copy())

    source_locations = torch.zeros(1, 1, 2, dtype=torch.long)
    source_locations[0, 0, 0] = src_depth
    source_locations[0, 0, 1] = src_x

    receiver_locations = torch.zeros(1, nx, 2, dtype=torch.long)
    receiver_locations[0, :, 0] = REC_DEPTH
    receiver_locations[0, :, 1] = torch.arange(nx)

    source_amplitudes = (
        deepwave.wavelets.ricker(f0, nt, dt, 1.5 / f0)
        .reshape(1, 1, -1)
    )

    snap_set = frozenset(snap_its)
    snapshots: dict[int, NDArray] = {}

    def callback(state):
        step = state.step
        if step in snap_set:
            wf = state.get_wavefield("wavefield_0")
            if wf.numel() > 0:
                snap = wf[0].cpu().numpy() if wf.ndim == 3 else wf.cpu().numpy()
                snapshots[step] = snap.copy()

    deepwave.scalar(
        v, dx, dt,
        source_amplitudes=source_amplitudes,
        source_locations=source_locations,
        receiver_locations=receiver_locations,
        accuracy=8,
        pml_freq=f0,
        forward_callback=callback,
        callback_frequency=1,
    )

    return snapshots


# ─── 伪谱法正演 ──────────────────────────────────────────────

def pseudo_spectral_2d(
    vel: NDArray,
    src_x: int,
    src_z: int,
    snap_its: tuple[int, ...] = (),
    f0: float = F0,
    dt: float = DT,
    nt: int = NT,
    dx: float = DX,
    absorb: int = ABSORB,
) -> tuple[NDArray, dict[int, NDArray]]:
    """伪谱法声波正演。"""
    nz, nx = vel.shape
    c2 = (vel * (dt / dx)) ** 2
    src = ricker(f0, dt, nt)

    sp = np.ones((nz, nx), dtype=np.float32)
    gamma = 0.015
    for i in range(absorb):
        val = float(np.exp(-((gamma * (absorb - i)) ** 2)))
        sp[i, :] *= val; sp[-(i+1), :] *= val
        sp[:, i] *= val; sp[:, -(i+1)] *= val

    kx = np.fft.fftfreq(nx, d=dx) * 2 * np.pi
    kz = np.fft.fftfreq(nz, d=dx) * 2 * np.pi
    KX, KZ = np.meshgrid(kx, kz)
    K2 = KX**2 + KZ**2

    p  = np.zeros((nz, nx), dtype=np.float32)
    pp = np.zeros((nz, nx), dtype=np.float32)
    record = np.zeros((nt, nx), dtype=np.float32)
    snaps: dict[int, NDArray] = {}
    snap_set = frozenset(snap_its)

    for it in range(nt):
        P = np.fft.fft2(p)
        lap = np.real(np.fft.ifft2(-K2 * P)).astype(np.float32)
        pn = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]
        pn *= sp
        record[it] = pn[REC_DEPTH, :]
        if it in snap_set:
            snaps[it] = pn.copy()
        pp[:] = p
        p[:] = pn

    return record, snaps


# ─── 辅助 ────────────────────────────────────────────────────

def smooth_shot(shot: NDArray, window: int = 15) -> NDArray:
    kernel = np.ones(window, dtype=np.float32) / window
    return np.apply_along_axis(
        lambda col: np.convolve(col, kernel, mode="same"),
        axis=0, arr=shot,
    ).astype(np.float32)


def gaussian_smooth_2d(arr: NDArray, sigma: float = 3.0) -> NDArray:
    from numpy.fft import fft2, ifft2
    nz, nx = arr.shape
    kz = np.fft.fftfreq(nz).reshape(-1, 1)
    kx = np.fft.fftfreq(nx).reshape(1, -1)
    gauss = np.exp(-2 * np.pi**2 * sigma**2 * (kz**2 + kx**2)).astype(np.float32)
    return np.real(ifft2(fft2(arr) * gauss)).astype(np.float32)


# ─── 主程序 ──────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {OUT_DIR}")
    print(f"Parameters: f0={F0} Hz, dx={DX} m, dt={DT} s, grid={NZ}x{NX}")
    print(f"Dispersion: lambda_min/dx = {1500/F0/DX:.1f} (need >= 10) OK")
    print(f"API: deepwave.scalar(accuracy=8, pml_freq={F0})\n")

    # ── 1. 速度模型 ──────────────────────────────────────────
    print("[1/6] Building velocity model ...")
    vel = make_velocity_model()
    np.save(OUT_DIR / "velocity_model.npy", vel)
    print(f"  shape={vel.shape}  v=[{vel.min():.0f}, {vel.max():.0f}] m/s")

    # ── 2. deepwave scalar() 炮记录 ──────────────────────────
    src_x = NX // 2
    print(f"\n[2/6] deepwave.scalar() shot records (f0={F0} Hz, accuracy=8) ...")
    t0 = time.perf_counter()
    shot = deepwave_shot_record(vel, src_x)
    t_dw = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_record.npy", shot)
    print(f"  shot_record.npy  shape={shot.shape}  ({t_dw:.2f} s)")

    src_x1 = NX // 5
    t0 = time.perf_counter()
    shot1 = deepwave_shot_record(vel, src_x1)
    t_dw1 = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_record_src1.npy", shot1)
    print(f"  shot_record_src1.npy  shape={shot1.shape}  ({t_dw1:.2f} s)")

    # ── 3. 平滑炮记录 ────────────────────────────────────────
    print("\n[3/6] Smoothed shot record ...")
    shot_s = smooth_shot(shot)
    np.save(OUT_DIR / "shot_smooth.npy", shot_s)

    # ── 4. deepwave 波场快照 ──────────────────────────────────
    snap_times = (200, 500, 750)
    print(f"\n[4/6] deepwave wavefield snapshots at steps {snap_times} ...")
    t0 = time.perf_counter()
    snaps_dw = deepwave_snapshots(vel, src_x, snap_its=snap_times)
    t_snap = time.perf_counter() - t0
    for it, snap in snaps_dw.items():
        t_label = int(it * DT * 1000)
        fname = f"snap_{t_label}ms.npy"
        np.save(OUT_DIR / fname, snap)
        print(f"  {fname}  shape={snap.shape}  range=[{snap.min():.1f}, {snap.max():.1f}]")
    print(f"  done in {t_snap:.2f} s")

    # ── 5. 多方法对比数据 ────────────────────────────────────
    print("\n[5/6] Multi-method comparison data (t=500 ms) ...")

    snap_ref = snaps_dw[500]
    np.save(OUT_DIR / "method_ps_ref.npy", snap_ref)
    print("  method_ps_ref.npy  (deepwave reference)")

    np.save(OUT_DIR / "method_deepwave.npy", snap_ref)
    print("  method_deepwave.npy  (same)")

    # 粗网格
    print("  Coarse grid (dx=20m) ...")
    vel_coarse = vel[::2, ::2]
    snaps_c = deepwave_snapshots(
        vel_coarse, NX // 4, snap_its=(500,),
        dx=DX * 2, dt=DT, nt=NT, f0=F0,
    )
    snap_c = snaps_c[500]
    snap_coarse = np.repeat(np.repeat(snap_c, 2, axis=0), 2, axis=1)[:NZ, :NX]
    np.save(OUT_DIR / "method_coarse.npy", snap_coarse)
    print(f"  method_coarse.npy  shape={snap_coarse.shape}")

    # 高斯平滑
    snap_sm = gaussian_smooth_2d(snap_ref, sigma=3.0)
    np.save(OUT_DIR / "method_smooth.npy", snap_sm)
    print("  method_smooth.npy  (Gaussian filtered)")

    # ── 6. 性能基准 ──────────────────────────────────────────
    print("\n[6/6] Performance benchmark (pseudo-spectral) ...")
    cats, vals = [], []
    for nz, nx in [(100, 200), (200, 400), (300, 600)]:
        v_ = make_velocity_model(nz, nx, DX)
        t0 = time.perf_counter()
        pseudo_spectral_2d(
            v_, nx // 2, REC_DEPTH, snap_its=(),
            dt=DT, nt=min(NT, 500), dx=DX, absorb=min(ABSORB, nz // 5),
        )
        elapsed = round(time.perf_counter() - t0, 3)
        cats.append(f"{nz}x{nx}")
        vals.append(elapsed)
        print(f"  grid {nz}x{nx}  -> {elapsed:.3f} s")

    with open(OUT_DIR / "perf.json", "w", encoding="utf-8") as f:
        json.dump(
            {"categories": cats, "values": vals, "metric_label": "Runtime (s)"},
            f, indent=2,
        )

    # ── 汇总 ─────────────────────────────────────────────────
    print(f"\n{'─' * 58}")
    print("All data saved:")
    for p in sorted(OUT_DIR.iterdir()):
        if p.suffix == ".npy":
            a = np.load(p)
            print(f"  {p.name:<28} shape={str(a.shape):<14} dtype={a.dtype}")
        elif p.is_file():
            print(f"  {p.name}")
    print(f"{'─' * 58}")


if __name__ == "__main__":
    main()
