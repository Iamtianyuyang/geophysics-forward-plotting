"""测试 PlottingAgent 基础路由和执行逻辑。"""

from geophysics_forward_plotting import PlottingAgent
from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.skills.registry import SkillRegistry


class VelocitySkill(BaseSkill):
    def can_handle(self, task: FigureTask) -> bool:
        return task.task_type is TaskType.VELOCITY_MODEL

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        return FigureResult(summary="velocity model ready")

    def review(self, result: FigureResult) -> list[str]:
        return ["reviewed"]


def test_agent_executes_registered_skill() -> None:
    # 使用空注册表 + 关闭全局审查，只测试路由逻辑
    agent = PlottingAgent(
        registry=SkillRegistry([VelocitySkill("velocity", "Test skill")]),
        auto_review=False,
    )

    result = agent.run(FigureTask(task_type="velocity_model"))

    assert result.summary == "velocity model ready"
    assert result.review_messages == ["reviewed"]


def test_agent_default_registry_has_skills() -> None:
    agent = PlottingAgent()
    names = agent.available_skills()
    assert "velocity_model" in names
    assert "shot_record" in names
    assert "multi_method_compare" in names
    assert "performance" in names
    assert "figure_review" in names


def test_agent_auto_review_adds_messages() -> None:
    # 任务缺少 colorbar_label，审查器应给出警告
    agent = PlottingAgent(
        registry=SkillRegistry([VelocitySkill("velocity", "Test")]),
        auto_review=True,
    )
    task = FigureTask(task_type="velocity_model")  # 无 colorbar_label
    result = agent.run(task)
    # skill 的 review 消息 + 全局规范检查消息
    assert any("colorbar_label" in m for m in result.review_messages)
