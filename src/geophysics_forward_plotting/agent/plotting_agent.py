"""PlottingAgent：核心编排器，连接 Planner → TaskRouter → Skill → Review。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from geophysics_forward_plotting.agent.review import run_review
from geophysics_forward_plotting.agent.task_router import TaskRouter
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.skills.registry import SkillRegistry


def _build_default_registry() -> SkillRegistry:
    """注册所有内置技能，返回默认 SkillRegistry。"""
    from geophysics_forward_plotting.skills.data_inspector_skill import DataInspectorSkill
    from geophysics_forward_plotting.skills.error_map_skill import ErrorMapSkill
    from geophysics_forward_plotting.skills.export_skill import ExportSkill
    from geophysics_forward_plotting.skills.figure_review_skill import FigureReviewSkill
    from geophysics_forward_plotting.skills.multi_method_compare_skill import (
        MultiMethodCompareSkill,
    )
    from geophysics_forward_plotting.skills.performance_skill import PerformanceSkill
    from geophysics_forward_plotting.skills.shot_record_skill import ShotRecordSkill
    from geophysics_forward_plotting.skills.sliceviewer_skill import SliceViewerSkill
    from geophysics_forward_plotting.skills.style_skill import StyleSkill
    from geophysics_forward_plotting.skills.velocity_model_skill import VelocityModelSkill
    from geophysics_forward_plotting.skills.volume_3d_skill import Volume3DSkill
    from geophysics_forward_plotting.skills.wavefield_snapshot_skill import WavefieldSnapshotSkill
    from geophysics_forward_plotting.skills.wiggle_skill import WiggleSkill

    return SkillRegistry(
        [
            DataInspectorSkill(),
            VelocityModelSkill(),
            ShotRecordSkill(),
            WavefieldSnapshotSkill(),
            MultiMethodCompareSkill(),
            WiggleSkill(),
            ErrorMapSkill(),
            PerformanceSkill(),
            Volume3DSkill(),
            SliceViewerSkill(),
            StyleSkill(),
            FigureReviewSkill(),
            ExportSkill(),
        ]
    )


@dataclass(slots=True)
class PlottingAgent:
    """
    接收 FigureTask，路由到合适的 Skill，执行绘图，
    并运行 FigureReviewSkill 对结果进行规范检查。

    用法示例
    --------
    >>> from geophysics_forward_plotting import PlottingAgent, FigureTask
    >>> agent = PlottingAgent()
    >>> task = FigureTask(task_type="velocity_model", data_paths=["velocity_model.npy"])
    >>> result = agent.run(task)
    """

    registry: SkillRegistry = field(default_factory=_build_default_registry)
    auto_review: bool = True  # 每次 run 后自动执行规范检查

    def register(self, skill: BaseSkill, *, replace: bool = False) -> None:
        self.registry.register(skill, replace=replace)

    def available_skills(self) -> tuple[str, ...]:
        return self.registry.names()

    def run(
        self,
        task: FigureTask,
        context: DataContext | None = None,
    ) -> FigureResult:
        """执行任务并返回结果（含规范检查消息）。"""
        # Always inspect: direct arrays also need a stable layout before rendering.
        from geophysics_forward_plotting.skills.data_inspector_skill import DataInspectorSkill

        source_context = context or DataContext()
        insp_result = DataInspectorSkill().run(task, source_context)
        ctx = insp_result.metadata.get("context", source_context)

        router = TaskRouter(self.registry)
        skill = router.route(task)
        result = skill.run(task, ctx)
        result.review_messages.extend(skill.review(result))

        # 全局规范检查
        if self.auto_review:
            review_msgs = run_review(task, result)
            result.review_messages.extend(review_msgs)

        return result

    def run_from_yaml(self, config_path: str | Path) -> FigureResult:
        """从 YAML 配置文件加载任务并执行。"""
        from geophysics_forward_plotting.agent.planner import Planner

        task = Planner.from_yaml(config_path)
        return self.run(task)
