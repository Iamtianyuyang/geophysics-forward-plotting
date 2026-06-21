"""图件导出工具：处理多格式保存和路径生成。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_figure(
    fig: Any,
    stem: str,
    output_dir: Path,
    formats: tuple[str, ...],
    dpi: int = 600,
) -> list[Path]:
    """将 matplotlib Figure 保存为指定格式，返回所有保存路径。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for fmt in formats:
        dest = output_dir / f"{stem}.{fmt}"
        fig.savefig(dest, dpi=dpi, bbox_inches="tight")
        saved.append(dest)
    return saved
