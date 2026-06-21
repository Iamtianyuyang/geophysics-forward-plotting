#!/usr/bin/env python3
"""
用 deepwave + NumPy FDTD 生成全套示例数据。

依赖
  pip install deepwave torch matplotlib

产出 examples/data/
  velocity_model.npy       (200, 400)  五层速度模型（含倾斜界面、低速异常体）
  shot_record.npy          (1000, 400) deepwave 声波正演炮记录（震源居中）
  shot_record_src1.npy     (1000, 400) deepwave 炮记录（震源偏移）
  snap_200ms.npy           (200, 400)  NumPy FDTD 波场快照 t=0.2 s
  snap_500ms.npy           (200, 400)  波场快照 t=0.5 s
  snap_750ms.npy           (200, 400)  波场快照 t=0.75 s
  shot_smooth.npy          (1000, 400) 平滑炮记录（模拟低频方法）
  method_fd_fine.npy       (200, 400)  FD 精细网格波场快照 t=0.5 s
  method_fd_coarse.npy     (200, 400)  FD 粗网格波场快照 t=0.5 s
  method_smooth.npy        (200, 400)  高斯平滑波场快照 t=0.5 s
  method_perturbed.npy     (200, 400)  速度扰动波场快照 t=0.5 s
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

# ─── 路径 ────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

OUT_DIR = REPO / "examples" / "data"

# ─── 仿真参数 ────────────────────────────────────────────────
NZ, NX   = 200, 400      # 深度 × 横向网格点数
DX       = 10.0           # 空间步长 (m)
DT       = 0.001          # 时间步长 (s)
NT       = 1000           # 时间步数 → 1.0 s
F0       = 25.0           # Ricker 子波主频 (Hz)
ABSORB   = 30             # 吸收边界宽度（网格点）
REC_Z    = 2              # 接收道深度行


# ─── 速度模型 ────────────────────────────────────────────────

def make_velocity_model(
    nz: int = NZ,
    nx: int = NX,
    dx: float = DX,
) -> NDArray:
    """
    构建五层速度模型：
      Layer 0 : 0–40 行   v ≈ 1500 m/s  （水层）
      Layer 1 : 40–80 行  v ≈ 2200 m/s  （浅沉积）
      Layer 2 : 80–120 行 v ≈ 2800 m/s  （中沉积）
      Layer 3 : 120–160 行 v ≈ 3400 m/s  （深沉积）
      Layer 4 : 160+ 行    v ≈ 4000 m/s  （基底）

    加入：
      - 正弦倾斜界面（±12 网格点振幅）
      - 高斯低速异常体（位于模型中部偏左，v -= 500 m/s）
      - 横向速度梯度（+200 m/s 从左到右）
    """
    base_velocities = [1500.0, 2200.0, 2800.0, 3400.0, 4000.0]
    layer_boundaries = [40, 80, 120, 160]  # 界面行号

    # 正弦倾斜界面
    x = np.arange(nx, dtype=np.float32)
    shifted_boundaries = []
    for ib in layer_boundaries:
        shift = (12 * np.sin(2 * np.pi * x / nx + ib * 0.05)).astype(int)
        shifted_boundaries.append(ib + shift)  # shape (nx,)

    # 逐列计算层号：计数有多少个界面在当前行之下
    vel = np.empty((nz, nx), dtype=np.float32)
    for ix in range(nx):
        for iz in range(nz):
            layer = sum(1 for sb in shifted_boundaries if iz >= sb[ix])
            vel[iz, ix] = base_velocities[min(layer, len(base_velocities) - 1)]

    # 高斯低速异常体（模拟含气砂岩或溶洞）
    cx, cz = nx // 4, nz // 3     # 中心位置
    sx, sz = nx // 8, nz // 10    # 半宽
    zz, xx = np.ogrid[:nz, :nx]
    mask = ((zz - cz) ** 2 / sz**2 + (xx - cx) ** 2 / sx**2) < 1
    vel[mask] -= 500.0

    # 横向梯度（右侧速度略高，模拟压实效应）
    gradient = np.linspace(0, 200, nx, dtype=np.float32)
    vel += gradient[np.newaxis, :]

    # 确保最低速度不低于 1400 m/s
    vel = np.maximum(vel, 1400.0)

    return vel


# ─── NumPy FDTD 正演（用于波场快照） ─────────────────────────

def ricker_wavelet(f0: float, dt: float, nt: int) -> NDArray:
    t  = np.arange(nt, dtype=np.float64) * dt
    t0 = 1.5 / f0
    x  = np.pi * f0 * (t - t0)
    return ((1.0 - 2.0 * x**2) * np.exp(-(x**2))).astype(np.float32)


def make_sponge(nz: int, nx: int, width: int, gamma: float = 0.015) -> NDArray:
    s = np.ones((nz, nx), dtype=np.float32)
    for i in range(width):
        val = float(np.exp(-((gamma * (width - i)) ** 2)))
        s[i,       :] *= val
        s[-(i + 1), :] *= val
        s[:,        i] *= val
        s[:, -(i + 1)] *= val
    return s


def fdtd2d_snapshots(
    vel: NDArray,
    src_x: int,
    src_z: int,
    snap_its: tuple[int, ...],
    f0: float = F0,
    dt: float = DT,
    nt: int = NT,
    dx: float = DX,
    absorb: int = ABSORB,
) -> dict[int, NDArray]:
    """
    二阶声波 FDTD，仅返回波场快照（不保存炮记录）。
    """
    nz, nx = vel.shape
    c2 = (vel * (dt / dx)) ** 2
    sp = make_sponge(nz, nx, absorb)
    src = ricker_wavelet(f0, dt, nt)

    p  = np.zeros((nz, nx), dtype=np.float32)
    pp = np.zeros((nz, nx), dtype=np.float32)
    snaps: dict[int, NDArray] = {}
    snap_set = frozenset(snap_its)

    for it in range(nt):
        lap = np.zeros_like(p)
        lap[1:-1, 1:-1] = (
            p[2:,   1:-1] + p[:-2,  1:-1]
          + p[1:-1, 2:  ] + p[1:-1, :-2 ]
          - 4.0 * p[1:-1, 1:-1]
        )
        pn = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]
        pn *= sp

        if it in snap_set:
            snaps[it] = pn.copy()

        pp[:] = p
        p[:]  = pn

    return snaps


# ─── deepwave 炮记录 ─────────────────────────────────────────

def deepwave_shot_record(
    vel: NDArray,
    src_x: int,
    src_z: int,
    dx: float = DX,
    dt: float = DT,
    nt: int = NT,
    f0: float = F0,
    pml_width: int = ABSORB,
) -> NDArray:
    """用 deepwave 声波正演生成炮记录 (nt, nx)。"""
    import torch
    import deepwave as dw

    nz, nx = vel.shape

    vel_t = torch.from_numpy(vel).unsqueeze(0)  # (1, nz, nx)
    rho_t = torch.ones(1, nz, nx) * 1000.0

    model = dw.Acoustic(vel_t, rho_t, grid_spacing=dx)

    src_amp = dw.wavelets.ricker(f0, nt, dt, 1.5 / f0).reshape(1, 1, -1)
    src_loc = torch.tensor([[[src_z, src_x]]])
    rec_loc = torch.tensor([[[REC_Z, i] for i in range(nx)]])

    out = model(
        dt=dt,
        source_amplitudes_p=src_amp,
        source_locations_p=src_loc,
        receiver_locations_p=rec_loc,
        pml_width=pml_width,
    )

    # out[7] 是接收器数据: (1, n_rec, nt) → 转置为 (nt, n_rec)
    shot = out[7][0].numpy().T.astype(np.float32)
    return shot


# ─── 辅助 ────────────────────────────────────────────────────

def smooth_shot(shot: NDArray, window: int = 11) -> NDArray:
    kernel = np.ones(window, dtype=np.float32) / window
    return np.apply_along_axis(
        lambda col: np.convolve(col, kernel, mode="same"),
        axis=0, arr=shot,
    ).astype(np.float32)


def gaussian_smooth_2d(arr: NDArray, sigma: float = 3.0) -> NDArray:
    """简单二维高斯平滑（无 scipy 依赖）。"""
    from numpy.fft import fft2, ifft2

    nz, nx = arr.shape
    kz = np.fft.fftfreq(nz).reshape(-1, 1)
    kx = np.fft.fftfreq(nx).reshape(1, -1)
    gauss = np.exp(-2 * np.pi**2 * sigma**2 * (kz**2 + kx**2)).astype(np.float32)
    return np.real(ifft2(fft2(arr) * gauss)).astype(np.float32)


# ─── 主程序 ──────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {OUT_DIR}\n")

    # ── 1. 速度模型 ──────────────────────────────────────────
    print("[1/6] Building velocity model (200x400) ...")
    vel = make_velocity_model()
    np.save(OUT_DIR / "velocity_model.npy", vel)
    print(f"  shape={vel.shape}  v=[{vel.min():.0f}, {vel.max():.0f}] m/s")

    # ── 2. deepwave 炮记录 ───────────────────────────────────
    src_x, src_z = NX // 2, REC_Z  # 震源居中，近地表
    print(f"\n[2/6] deepwave forward modeling (src at x={src_x}, z={src_z}) ...")
    t0 = time.perf_counter()
    shot = deepwave_shot_record(vel, src_x, src_z)
    t_dw = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_record.npy", shot)
    print(f"  shape={shot.shape}  range=[{shot.min():.2f}, {shot.max():.2f}]")
    print(f"  done in {t_dw:.2f} s")

    # 偏移震源炮记录
    src_x1 = NX // 5
    print(f"\n  deepwave forward (src at x={src_x1}, z={src_z}) ...")
    t0 = time.perf_counter()
    shot1 = deepwave_shot_record(vel, src_x1, src_z)
    t_dw1 = time.perf_counter() - t0
    np.save(OUT_DIR / "shot_record_src1.npy", shot1)
    print(f"  shape={shot1.shape}  done in {t_dw1:.2f} s")

    # ── 3. 平滑炮记录 ────────────────────────────────────────
    print("\n[3/6] Generating smoothed shot record ...")
    shot_s = smooth_shot(shot, window=15)
    np.save(OUT_DIR / "shot_smooth.npy", shot_s)
    print(f"  shape={shot_s.shape}")

    # ── 4. NumPy FDTD 波场快照 ───────────────────────────────
    snap_times = (200, 500, 750)
    print(f"\n[4/6] NumPy FDTD wavefield snapshots at {snap_times} steps ...")
    t0 = time.perf_counter()
    snaps = fdtd2d_snapshots(vel, src_x, src_z, snap_its=snap_times)
    t_fd = time.perf_counter() - t0
    for it, snap in snaps.items():
        fname = f"snap_{it}ms.npy" if it in (200, 500, 750) else f"snap_{it}.npy"
        # snap_times 是时间步索引，对应时间 = it * DT
        t_label = int(it * DT * 1000)
        fname = f"snap_{t_label}ms.npy"
        np.save(OUT_DIR / fname, snap)
        print(f"  {fname}  shape={snap.shape}")
    print(f"  done in {t_fd:.2f} s")

    # ── 5. 多方法对比数据（波场快照 t=500ms） ─────────────────
    print("\n[5/6] Multi-method comparison data (wavefield at t=500ms) ...")
    snap_ref = snaps[500]   # 参考：精细网格 FDTD
    np.save(OUT_DIR / "method_fd_fine.npy", snap_ref)
    print("  method_fd_fine.npy  (reference)")

    # FD-coarse: 粗网格速度 + FDTD
    vel_coarse = vel[::2, ::2]  # (100, 200), dx=20m
    snaps_c = fdtd2d_snapshots(
        vel_coarse, NX // 4, REC_Z,
        snap_its=(250,), dt=DT, nt=NT, dx=DX * 2, absorb=ABSORB // 2,
    )
    snap_coarse = snaps_c[250]
    # 上采样到原始网格尺寸
    from numpy import repeat as nrepeat
    snap_coarse_up = nrepeat(nrepeat(snap_coarse, 2, axis=0), 2, axis=1)
    snap_coarse_up = snap_coarse_up[:NZ, :NX]
    np.save(OUT_DIR / "method_fd_coarse.npy", snap_coarse_up)
    print("  method_fd_coarse.npy  (coarse grid)")

    # Smoothed: 高斯平滑
    snap_smooth = gaussian_smooth_2d(snap_ref, sigma=3.0)
    np.save(OUT_DIR / "method_smooth.npy", snap_smooth)
    print("  method_smooth.npy  (Gaussian filtered)")

    # Perturbed: 速度扰动（+5% 随机噪声速度模型）
    rng = np.random.default_rng(42)
    vel_pert = vel * (1 + rng.normal(0, 0.05, vel.shape)).astype(np.float32)
    vel_pert = np.maximum(vel_pert, 1400.0)
    snaps_p = fdtd2d_snapshots(vel_pert, src_x, src_z, snap_its=(500,))
    snap_pert = snaps_p[500]
    np.save(OUT_DIR / "method_perturbed.npy", snap_pert)
    print("  method_perturbed.npy  (perturbed velocity)")

    # ── 6. 性能基准 ──────────────────────────────────────────
    print("\n[6/6] Performance benchmark (varying grid size) ...")
    cats, vals = [], []
    for nz, nx in [(100, 200), (200, 400), (300, 600)]:
        v_ = make_velocity_model(nz, nx, DX)
        t0 = time.perf_counter()
        fdtd2d_snapshots(
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
        else:
            print(f"  {p.name}")
    print(f"{'─' * 58}")


if __name__ == "__main__":
    main()
