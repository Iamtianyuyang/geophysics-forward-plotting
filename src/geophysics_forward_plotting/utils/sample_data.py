"""生成示例 mock 数据，供 examples/ 脚本在无 deepwave 环境下使用。

注意：推荐使用 generate_data.py 生成基于 deepwave 的高质量数据。
此模块仅作为后备方案，当 generate_data.py 未运行时提供基础数据。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def _build_velocity_model(nz: int = 200, nx: int = 400) -> NDArray:
    """五层倾斜速度模型 (nz, nx)，单位 m/s。"""
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

    vel += np.linspace(0, 200, nx, dtype=np.float32)[np.newaxis, :]
    vel = np.maximum(vel, 1400.0)
    return vel


def _ricker_wavelet(nt: int, dt: float, f0: float = 15.0) -> NDArray:
    t = np.arange(nt, dtype=float) * dt
    t0 = 1.5 / f0
    x = np.pi * f0 * (t - t0)
    return ((1 - 2 * x**2) * np.exp(-(x**2))).astype(np.float32)


def _make_sponge(nz: int, nx: int, width: int = 30) -> NDArray:
    s = np.ones((nz, nx), dtype=np.float32)
    for i in range(width):
        val = float(np.exp(-((0.015 * (width - i)) ** 2)))
        s[i, :] *= val
        s[-(i + 1), :] *= val
        s[:, i] *= val
        s[:, -(i + 1)] *= val
    return s


def _fdtd_shot_record(vel: NDArray, nt: int = 1000, dt: float = 0.001,
                      dx: float = 10.0, f0: float = 15.0) -> NDArray:
    """简化伪谱法生成炮记录 (nt, nx)。"""
    nz, nx = vel.shape
    c2 = (vel * (dt / dx)) ** 2
    sp = _make_sponge(nz, nx)
    src = _ricker_wavelet(nt, dt, f0)
    src_x, src_z = nx // 2, 2

    # 波数
    kx = np.fft.fftfreq(nx, d=dx) * 2 * np.pi
    kz = np.fft.fftfreq(nz, d=dx) * 2 * np.pi
    KX, KZ = np.meshgrid(kx, kz)
    K2 = KX**2 + KZ**2

    p = np.zeros((nz, nx), dtype=np.float32)
    pp = np.zeros((nz, nx), dtype=np.float32)
    record = np.zeros((nt, nx), dtype=np.float32)

    for it in range(nt):
        P = np.fft.fft2(p)
        lap = np.real(np.fft.ifft2(-K2 * P)).astype(np.float32)
        pn = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]
        pn *= sp
        record[it] = pn[1, :]
        pp[:] = p
        p[:] = pn

    return record


def make_velocity_model(nz: int = 200, nx: int = 400) -> NDArray:
    return _build_velocity_model(nz, nx)


def make_shot_record(nt: int = 1000, nx: int = 400, dt: float = 0.001) -> NDArray:
    """用 FDTD 生成合成炮记录 (nt, nx)。"""
    vel = _build_velocity_model(200, nx)
    return _fdtd_shot_record(vel, nt, dt)


def make_wavefield_snapshot(nz: int = 200, nx: int = 400) -> NDArray:
    """用伪谱法生成 t=500ms 波场快照 (nz, nx)。"""
    vel = _build_velocity_model(nz, nx)
    dx = 10.0
    dt = 0.001
    c2 = (vel * (dt / dx)) ** 2
    sp = _make_sponge(nz, nx)
    src = _ricker_wavelet(1000, dt)
    src_x, src_z = nx // 2, 2

    kx = np.fft.fftfreq(nx, d=dx) * 2 * np.pi
    kz = np.fft.fftfreq(nz, d=dx) * 2 * np.pi
    KX, KZ = np.meshgrid(kx, kz)
    K2 = KX**2 + KZ**2

    p = np.zeros((nz, nx), dtype=np.float32)
    pp = np.zeros((nz, nx), dtype=np.float32)

    for it in range(500):
        P = np.fft.fft2(p)
        lap = np.real(np.fft.ifft2(-K2 * P)).astype(np.float32)
        pn = 2.0 * p - pp + c2 * lap
        pn[src_z, src_x] += src[it]
        pn *= sp
        pp[:] = p
        p[:] = pn

    return p


def make_volume_3d(nz: int = 30, ny: int = 30, nx: int = 60) -> NDArray:
    """生成三维地震体 (nz, ny, nx)。"""
    zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]
    v = np.sin(0.3 * xx) * np.cos(0.4 * yy) * np.exp(-0.05 * zz)
    return v.astype(np.float32)


def make_method_results(nz: int = 200, nx: int = 400) -> list[NDArray]:
    """生成四个方法的波场快照（物理上不同的结果）。"""
    base = make_wavefield_snapshot(nz, nx)  # pseudo-spectral reference

    # Deepwave standard (same grid, slightly different due to numerics)
    # Approximate by adding small perturbation to represent numerical difference
    rng = np.random.default_rng(42)
    perturbation = rng.normal(0, 0.001 * np.abs(base).max(), base.shape)
    deepwave_approx = base + perturbation.astype(np.float32)

    # Coarse: downsample + upsample
    coarse = base[::2, ::2]
    coarse_up = np.repeat(np.repeat(coarse, 2, axis=0), 2, axis=1)[:nz, :nx]

    # Smoothed: Gaussian low-pass
    from numpy.fft import fft2, ifft2
    kz = np.fft.fftfreq(nz).reshape(-1, 1)
    kx = np.fft.fftfreq(nx).reshape(1, -1)
    gauss = np.exp(-2 * np.pi**2 * 9 * (kz**2 + kx**2)).astype(np.float32)
    smoothed = np.real(ifft2(fft2(base) * gauss)).astype(np.float32)

    return [base, deepwave_approx, coarse_up, smoothed]


def ensure_example_data(data_dir: Path) -> None:
    """生成所有示例 .npy 数据文件（若不存在则创建）。"""
    data_dir.mkdir(parents=True, exist_ok=True)

    specs: dict[str, NDArray] = {}

    if not (data_dir / "velocity_model.npy").exists():
        specs["velocity_model.npy"] = make_velocity_model()

    if not (data_dir / "shot_record.npy").exists():
        specs["shot_record.npy"] = make_shot_record()

    if not (data_dir / "snap_500ms.npy").exists():
        specs["snap_500ms.npy"] = make_wavefield_snapshot()

    if not (data_dir / "volume_3d.npy").exists():
        specs["volume_3d.npy"] = make_volume_3d()

    method_names = ["method_ps_ref.npy", "method_deepwave.npy",
                    "method_coarse.npy", "method_smooth.npy"]
    if not any((data_dir / n).exists() for n in method_names):
        methods = make_method_results()
        for name, arr in zip(method_names, methods, strict=True):
            specs[name] = arr

    for filename, arr in specs.items():
        dest = data_dir / filename
        if not dest.exists():
            np.save(dest, arr)
