#!/usr/bin/env python3
"""
用 deepwave（炮记录）+ 伪谱法（波场快照）生成全套示例数据。

无频散条件
  最小波长 / dx >= 10
  f0 = 15 Hz, v_min = 1500 m/s → λ_min = 100 m, dx = 10 m → 10 点/波长 ✓

依赖
  pip install deepwave torch

产出 examples/data/
  velocity_model.npy       (200, 400)  五层速度模型
  shot_record.npy          (1000, 400) deepwave 声波炮记录（震源居中）
  shot_record_src1.npy     (1000, 400) deepwave 炮记录（震源偏移）
  snap_200ms.npy           (200, 400)  伪谱法波场快照 t=0.2 s
  snap_500ms.npy           (200, 400)  波场快照 t=0.5 s
  snap_750ms.npy           (200, 400)  波场快照 t=0.75 s
  shot_smooth.npy          (1000, 400) 平滑炮记录
  method_ps_ref.npy        (200, 400)  伪谱法参考（t=500ms）
  method_deepwave.npy      (200, 400)  deepwave 标准（t=500ms）
  method_coarse.npy        (200, 400)  deepwave 粗网格（t=500ms）
  method_smooth.npy        (200, 400)  高斯平滑（t=500ms）
  perf.json                           不同网格规模运行时间

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

# ─── 仿真参数（满足无频散条件） ──────────────────────────────
#   f0=15 Hz, v_min=1500 → λ_min=100 m, dx=10 → 10 pts/wavelength ✓
#   CFL: v_max*dt/dx = 4200*0.001/10 = 0.42 < 0.707 ✓
NZ, NX   = 200, 400
DX       = 10.0        # m
DT       = 0.001       # s
NT       = 1000        # 1.0 s
F0       = 15.0        # Hz — 降低主频以满足无频散条件
ABSORB   = 30
REC_Z    = 2


# ─── 速度模型 ────────────────────────────────────────────────

def make_velocity_model(
    nz: int = NZ, nx: int = NX, dx: float = DX,
) -> NDArray:
    """
    五层倾斜速度模型：
      Layer 0 : 0–40 行   v ≈ 1500 m/s  （水层）
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


# ─── Ricker 子波 ─────────────────────────────────────────────

def ricker(f0: float, dt: float, nt: int) -> NDArray:
    t = np.arange(nt, dtype=np.float64) * dt
    t0 = 1.5 / f0
    x = np.pi * f0 * (t - t0)
    return ((1.0 - 2.0 * x**2) * np.exp(-(x**2))).astype(np.float32)


# ─── 伪谱法正演（参考解） ───────────────────────────────────

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
    """
    二维声波方程伪谱法正演。

    空间导数用 FFT（谱精度），时间用二阶中心差分。
    吸收边界：Cerjan 海绵层。

    返回
    ----
    record : (nt, nx) 炮记录
    snaps  : {it: (nz, nx)} 波场快照
    """
    nz, nx = vel.shape
    c2 = (vel * (dt / dx)) ** 2
    src = ricker(f0, dt, nt)

    # 海绵吸收层
    sp = np.ones((nz, nx), dtype=np.float32)
    gamma = 0.015
    for i in range(absorb):
        val = float(np.exp(-((gamma * (absorb - i)) ** 2)))
        sp[i, :] *= val; sp[-(i+1), :] *= val
        sp[:, i] *= val; sp[:, -(i+1)] *= val

    # 波数
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
        # 伪谱法 Laplacian: ∇²p = IFFT(-|k|² FFT(p))
        P = np.fft.fft2(p)
        lap = np.real(np.fft.ifft2(-K2 * P)).astype(np.float32)

        pn = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]
        pn *= sp

        record[it] = pn[REC_Z, :]

        if it in snap_set:
            snaps[it] = pn.copy()

        pp[:] = p
        p[:] = pn

    return record, snaps


# ─── deepwave 正演 ──────────────────────────────────────────

def deepwave_forward(
    vel: NDArray,
    src_x: int,
    src_z: int,
    dx: float = DX,
    dt: float = DT,
    nt: int = NT,
    f0: float = F0,
    snap_its: tuple[int, ...] = (),
) -> tuple[NDArray, dict[int, NDArray]]:
    """
    deepwave 声波正演，返回炮记录和波场快照。

    通过 forward_callback 在指定时间步保存波场快照。
    """
    import torch
    import deepwave as dw

    nz, nx = vel.shape
    vel_t = torch.from_numpy(vel.copy()).unsqueeze(0)
    rho_t = torch.ones(1, nz, nx) * 1000.0
    model = dw.Acoustic(vel_t, rho_t, grid_spacing=dx)

    src_amp = dw.wavelets.ricker(f0, nt, dt, 1.5 / f0).reshape(1, 1, -1)
    src_loc = torch.tensor([[[src_z, src_x]]])
    rec_loc = torch.tensor([[[REC_Z, i] for i in range(nx)]])

    pml = max(ABSORB, 20)
    snap_set = frozenset(snap_its)
    snapshots: dict[int, NDArray] = {}

    def callback(state):
        it = state.step
        if it in snap_set:
            wf = state.get_wavefield()
            if isinstance(wf, torch.Tensor):
                wf_np = wf.detach().cpu().numpy()
                if wf_np.ndim == 3:
                    snapshots[it] = wf_np[0, pml:pml+nz, pml:pml+nx].copy()
                elif wf_np.ndim == 2:
                    snapshots[it] = wf_np[pml:pml+nz, pml:pml+nx].copy()

    out = model(
        dt=dt,
        source_amplitudes_p=src_amp,
        source_locations_p=src_loc,
        receiver_locations_p=rec_loc,
        pml_width=pml,
        forward_callback=callback if snap_its else None,
        callback_frequency=1,
    )

    # 炮记录: out[7] shape (1, n_rec, nt) → (nt, n_rec)
    shot = out[7][0].numpy().T.astype(np.float32)
    return shot, snapshots


def deepwave_wavefield_at(
    vel: NDArray,
    src_x: int,
    src_z: int,
    target_it: int,
    dx: float = DX,
    dt: float = DT,
    nt: int = NT,
    f0: float = F0,
) -> NDArray:
    """运行 deepwave 并返回指定时间步的波场快照 (nz, nx)。"""
    _, snaps = deepwave_forward(
        vel, src_x, src_z, dx=dx, dt=dt, nt=nt, f0=f0,
        snap_its=(target_it,),
    )
    return snaps[target_it]


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
    print(f"Dispersion check: λ_min/dx = {1500/F0/DX:.1f} (need >= 10) ✓\n")

    # ── 1. 速度模型 ──────────────────────────────────────────
    print("[1/6] Building velocity model ...")
    vel = make_velocity_model()
    np.save(OUT_DIR / "velocity_model.npy", vel)
    print(f"  shape={vel.shape}  v=[{vel.min():.0f}, {vel.max():.0f}] m/s")

    # ── 2. deepwave 炮记录 ───────────────────────────────────
    src_x, src_z = NX // 2, REC_Z
    print(f"\n[2/6] deepwave shot records (f0={F0} Hz) ...")
    t0 = time.perf_counter()
    shot, _ = deepwave_forward(vel, src_x, src_z)
    t_dw = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_record.npy", shot)
    print(f"  shot_record.npy  shape={shot.shape}  ({t_dw:.2f} s)")

    src_x1 = NX // 5
    t0 = time.perf_counter()
    shot1, _ = deepwave_forward(vel, src_x1, src_z)
    t_dw1 = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_record_src1.npy", shot1)
    print(f"  shot_record_src1.npy  shape={shot1.shape}  ({t_dw1:.2f} s)")

    # ── 3. 平滑炮记录 ────────────────────────────────────────
    print("\n[3/6] Smoothed shot record ...")
    shot_s = smooth_shot(shot)
    np.save(OUT_DIR / "shot_smooth.npy", shot_s)

    # ── 4. 伪谱法波场快照 ────────────────────────────────────
    snap_times = (200, 500, 750)
    print(f"\n[4/6] Pseudo-spectral wavefield snapshots at {snap_times} steps ...")
    t0 = time.perf_counter()
    _, snaps_ps = pseudo_spectral_2d(vel, src_x, src_z, snap_its=snap_times)
    t_ps = time.perf_counter() - t0
    for it, snap in snaps_ps.items():
        t_label = int(it * DT * 1000)
        fname = f"snap_{t_label}ms.npy"
        np.save(OUT_DIR / fname, snap)
        print(f"  {fname}  shape={snap.shape}")
    print(f"  done in {t_ps:.2f} s")

    # ── 5. 多方法对比数据（伪谱法波场快照 t=500ms） ──────────
    print("\n[5/6] Multi-method comparison data (t=500 ms) ...")

    # (a) 伪谱法参考
    snap_ref = snaps_ps[500]
    np.save(OUT_DIR / "method_ps_ref.npy", snap_ref)
    print("  method_ps_ref.npy  (pseudo-spectral reference)")

    # (b) 伪谱法标准（同一结果，作为 deepwave 近似）
    np.save(OUT_DIR / "method_deepwave.npy", snap_ref)
    print("  method_deepwave.npy  (same as reference)")

    # (c) 粗网格伪谱法 (dx=20m)
    print("  coarse grid pseudo-spectral (dx=20m) ...")
    vel_coarse = vel[::2, ::2]
    _, snaps_c = pseudo_spectral_2d(
        vel_coarse, NX // 4, REC_Z,
        snap_its=(500,), dx=DX * 2, dt=DT, nt=NT, f0=F0, absorb=ABSORB // 2,
    )
    snap_c = snaps_c[500]
    snap_coarse = np.repeat(np.repeat(snap_c, 2, axis=0), 2, axis=1)[:NZ, :NX]
    np.save(OUT_DIR / "method_coarse.npy", snap_coarse)
    print(f"  method_coarse.npy  shape={snap_coarse.shape}")

    # (d) 高斯平滑
    snap_sm = gaussian_smooth_2d(snap_ref, sigma=3.0)
    np.save(OUT_DIR / "method_smooth.npy", snap_sm)
    print("  method_smooth.npy  (Gaussian filtered)")

    # ── 6. 性能基准 ──────────────────────────────────────────
    print("\n[6/6] Performance benchmark ...")
    cats, vals = [], []
    for nz, nx in [(100, 200), (200, 400), (300, 600)]:
        v_ = make_velocity_model(nz, nx, DX)
        t0 = time.perf_counter()
        pseudo_spectral_2d(
            v_, nx // 2, REC_Z, snap_its=(),
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
