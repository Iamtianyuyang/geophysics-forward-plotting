"""CIGVis-first geophysical forward-modeling plotting framework."""

from geophysics_forward_plotting.agent import (
    EvaluationReport,
    MethodEvaluationAgent,
    MethodResult,
    PlottingAgent,
)
from geophysics_forward_plotting.core.models import FigureResult, FigureTask
from geophysics_forward_plotting.skills.registry import SkillRegistry

__all__ = [
    "EvaluationReport",
    "FigureResult",
    "FigureTask",
    "MethodEvaluationAgent",
    "MethodResult",
    "PlottingAgent",
    "SkillRegistry",
]
__version__ = "0.1.0"

