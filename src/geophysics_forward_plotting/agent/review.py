"""ReviewPipeline：在绘图结果上运行 FigureReviewSkill。"""

from __future__ import annotations

from geophysics_forward_plotting.core.models import FigureResult, FigureTask
from geophysics_forward_plotting.skills.figure_review_skill import FigureReviewSkill

_REVIEWER = FigureReviewSkill()


def run_review(task: FigureTask, result: FigureResult) -> list[str]:
    """对已生成图件执行规范检查，返回警告/建议列表。"""
    task_msgs = _REVIEWER._check_task(task)
    fig_msgs = _REVIEWER.review(result)
    return task_msgs + fig_msgs
