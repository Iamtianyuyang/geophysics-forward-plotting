"""生成示例 mock 数据，供 examples/ 脚本直接使用。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def _marmousi_like_velocity(nz: int = 60, nx: int = 120) -> NDArray:
    """生成类似 Marmousi 模型的简化速度场 (nz, nx)，单位 m/s。"""
    v = np.ones((nz, nx), dtype=np.float32) * 1500.0
    for i in range(5):
        z0 = int(nz * (i + 1) / 6)
        v[z0:, :] += 200.0 * (i + 1)
    # 加一个低速透镜体
    z1, x1 = nz // 3, nx // 2
    zz, xx = np.ogrid[:nz, :nx]
    mask = ((zz - z1) ** 2 / 8**2 + (xx - x1) ** 2 / 20**2) < 1
    v[mask] -= 300.0
    return v


def _ricker_wavelet(nt: int = 300, dt: float = 0.002, f0: float = 20.0) -> NDArray:
    t = np.arange(nt, dtype=float) * dt - 0.1
    return ((1 - 2 * (np.pi * f0 * t) ** 2) * np.exp(-((np.pi * f0 * t) ** 2))).astype(np.float32)


def make_velocity_model(nz: int = 60, nx: int = 120) -> NDArray:
    return _marmousi_like_velocity(nz, nx)


def make_shot_record(nt: int = 300, nx: int = 120, dt: float = 0.002) -> NDArray:
    """生成合成炮记录 (nt, nx)。"""
    rng = np.random.default_rng(42)
    rec = np.zeros((nt, nx), dtype=np.float32)
    wav = _ricker_wavelet(nt, dt)
    for ix in range(nx):
        # 模拟不同炮检距的到达时间
        t_arr = int(30 + ix * 0.5)
        if t_arr + len(wav) < nt:
            rec[t_arr : t_arr + len(wav), ix] += wav * (1.0 - ix / (2 * nx))
    rec += rng.normal(0, 0.01, rec.shape).astype(np.float32)
    return rec


def make_wavefield_snapshot(nz: int = 60, nx: int = 120) -> NDArray:
    """生成单时间步波场快照 (nz, nx)。"""
    zz, xx = np.mgrid[0:nz, 0:nx]
    r = np.sqrt((zz - nz // 3) ** 2 + (xx - nx // 2) ** 2).astype(float)
    snap = np.sin(0.5 * r) * np.exp(-0.01 * r)
    return snap.astype(np.float32)


def make_volume_3d(nz: int = 30, ny: int = 30, nx: int = 60) -> NDArray:
    """生成三维地震体 (nz, ny, nx)。"""
    zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]
    v = np.sin(0.3 * xx) * np.cos(0.4 * yy) * np.exp(-0.05 * zz)
    return v.astype(np.float32)


def make_method_results(nz: int = 60, nx: int = 120, n: int = 4) -> list[NDArray]:
    """生成 n 个方法的合成波场结果（含轻微差异）。"""
    rng = np.random.default_rng(7)
    base = make_wavefield_snapshot(nz, nx)
    results = []
    for i in range(n):
        noise = rng.normal(0, 0.02 * (i + 1), base.shape).astype(np.float32)
        results.append(base + noise)
    return results


def ensure_example_data(data_dir: Path) -> None:
    """生成所有示例 .npy 数据文件（若不存在则创建）。"""
    data_dir.mkdir(parents=True, exist_ok=True)
    specs: dict[str, NDArray] = {
        "velocity_model.npy": make_velocity_model(),
        "shot_record.npy": make_shot_record(),
        "wavefield_snapshot.npy": make_wavefield_snapshot(),
        "volume_3d.npy": make_volume_3d(),
    }
    methods = make_method_results()
    for i, arr in enumerate(methods):
        specs[f"method_{chr(ord('a') + i)}.npy"] = arr

    for filename, arr in specs.items():
        dest = data_dir / filename
        if not dest.exists():
            np.save(dest, arr)
