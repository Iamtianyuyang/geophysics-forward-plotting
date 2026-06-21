"""Skill registration, discovery, and deterministic task resolution."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from geophysics_forward_plotting.core.exceptions import SkillRegistrationError
from geophysics_forward_plotting.core.models import FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill


class SkillRegistry:
    """Store skills by unique name and resolve them by priority."""

    def __init__(self, skills: Iterable[BaseSkill] | None = None) -> None:
        self._skills: dict[str, BaseSkill] = {}
        for skill in skills or ():
            self.register(skill)

    def register(self, skill: BaseSkill, *, replace: bool = False) -> None:
        if not isinstance(skill, BaseSkill):
            raise SkillRegistrationError("Only BaseSkill instances can be registered")
        if not skill.name.strip():
            raise SkillRegistrationError("Skill name must not be empty")
        if skill.name in self._skills and not replace:
            raise SkillRegistrationError(f"Skill already registered: {skill.name}")
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> BaseSkill:
        try:
            return self._skills.pop(name)
        except KeyError as exc:
            raise SkillRegistrationError(f"Skill is not registered: {name}") from exc

    def get(self, name: str) -> BaseSkill | None:
        return self._skills.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._skills))

    def matching(self, task: FigureTask) -> tuple[BaseSkill, ...]:
        matches = (skill for skill in self._skills.values() if skill.can_handle(task))
        return tuple(sorted(matches, key=lambda skill: (skill.priority, skill.name)))

    def resolve(self, task: FigureTask) -> BaseSkill | None:
        matches = self.matching(task)
        return matches[0] if matches else None

    def __contains__(self, name: object) -> bool:
        return name in self._skills

    def __len__(self) -> int:
        return len(self._skills)

    def __iter__(self) -> Iterator[BaseSkill]:
        return iter(sorted(self._skills.values(), key=lambda skill: (skill.priority, skill.name)))

