"""Base contract for executable plotting skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask


@dataclass(slots=True)
class BaseSkill(ABC):
    """Small, explicit skill contract used by the registry and agent."""

    name: str
    description: str
    priority: int = 100

    @abstractmethod
    def can_handle(self, task: FigureTask) -> bool:
        """Return whether this skill can execute the task."""

    @abstractmethod
    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        """Execute the skill and return a structured result."""

    def review(self, result: FigureResult) -> list[str]:
        """Return skill-local review messages; global review is added in Phase 3."""
        return []

