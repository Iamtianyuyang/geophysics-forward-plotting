"""Planner：从 YAML 配置或 Python dict 构建 FigureTask，支持批处理。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from geophysics_forward_plotting.core.exceptions import ConfigurationError
from geophysics_forward_plotting.core.models import FigureTask


class Planner:
    """从配置文件或字典构建可执行任务列表。"""

    @staticmethod
    def from_yaml(path: str | Path) -> FigureTask:
        """从单个 YAML 文件加载 FigureTask。"""
        source = Path(path)
        if not source.exists():
            raise ConfigurationError(f"配置文件不存在：{source}")
        with source.open("r", encoding="utf-8") as f:
            values: Any = yaml.safe_load(f)
        if not isinstance(values, dict):
            raise ConfigurationError("YAML 配置必须是一个 mapping")
        return FigureTask.from_mapping(values)

    @staticmethod
    def from_dict(values: dict[str, Any]) -> FigureTask:
        return FigureTask.from_mapping(values)

    @staticmethod
    def batch_from_yaml(paths: list[str | Path]) -> list[FigureTask]:
        """批量加载多个 YAML 配置，返回任务列表。"""
        return [Planner.from_yaml(p) for p in paths]
