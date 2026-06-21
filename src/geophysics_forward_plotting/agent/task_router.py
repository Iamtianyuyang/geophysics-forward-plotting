"""TaskRouter：根据 task_type 将任务路由到合适的 skill。"""

from __future__ import annotations

from geophysics_forward_plotting.core.exceptions import SkillNotFoundError
from geophysics_forward_plotting.core.models import FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.skills.registry import SkillRegistry


class TaskRouter:
    """封装 SkillRegistry.resolve 的路由层，提供更清晰的错误信息。"""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def route(self, task: FigureTask) -> BaseSkill:
        skill = self._registry.resolve(task)
        if skill is None:
            available = self._registry.names()
            raise SkillNotFoundError(
                f"没有注册的 Skill 可以处理任务类型 '{task.task_type}'。\n"
                f"当前已注册技能：{', '.join(available) or '（无）'}"
            )
        return skill
