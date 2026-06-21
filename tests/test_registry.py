import pytest

from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.exceptions import SkillRegistrationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.skills.registry import SkillRegistry


class ExampleSkill(BaseSkill):
    def can_handle(self, task: FigureTask) -> bool:
        return task.task_type is TaskType.VELOCITY_MODEL

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        return FigureResult(summary=self.name)


def test_registry_resolves_lowest_priority_first() -> None:
    registry = SkillRegistry(
        [
            ExampleSkill("fallback", "Fallback", priority=200),
            ExampleSkill("preferred", "Preferred", priority=10),
        ]
    )

    task = FigureTask(task_type=TaskType.VELOCITY_MODEL)

    resolved = registry.resolve(task)

    assert resolved is not None
    assert resolved.name == "preferred"
    assert registry.names() == ("fallback", "preferred")


def test_registry_rejects_duplicate_name() -> None:
    registry = SkillRegistry([ExampleSkill("velocity", "Velocity")])

    with pytest.raises(SkillRegistrationError, match="already registered"):
        registry.register(ExampleSkill("velocity", "Duplicate"))
