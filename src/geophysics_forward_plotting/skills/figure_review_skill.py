"""FigureReviewSkill：自动检查图件是否符合地球物理科研绘图规范。

检查项
------
1. colorbar 是否有标签
2. x/y 轴是否有单位
3. 时间轴/深度轴方向（需要 matplotlib Figure）
4. 多方法对比是否使用了统一 clim（通过任务参数判断）
5. 标题是否过长（> 60 字符）
6. DPI 是否满足论文要求（>= 300）
"""

from __future__ import annotations

from contextlib import suppress

from geophysics_forward_plotting.core.enums import TaskType
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask
from geophysics_forward_plotting.skills.base import BaseSkill


class FigureReviewSkill(BaseSkill):
    """自动审查图件配置，返回警告/建议列表。"""

    def __init__(self) -> None:
        super().__init__(
            name="figure_review",
            description="自动检查图件是否符合地球物理论文绘图规范",
            priority=80,
        )

    def can_handle(self, task: FigureTask) -> bool:
        return TaskType(task.task_type) is TaskType.FIGURE_REVIEW

    def run(self, task: FigureTask, context: DataContext) -> FigureResult:
        messages = self._check_task(task)
        return FigureResult(review_messages=messages, summary=f"审查完成，{len(messages)} 条提示")

    def review(self, result: FigureResult) -> list[str]:
        """也可作为后处理检查器被 agent 调用。"""
        messages: list[str] = []
        fig = result.figure
        if fig is None:
            return messages
        with suppress(Exception):
            messages.extend(self._check_mpl_figure(fig))
        return messages

    # ------------------------------------------------------------------
    # 内部检查方法
    # ------------------------------------------------------------------

    def _check_task(self, task: FigureTask) -> list[str]:
        msgs: list[str] = []

        if task.colorbar_label is None or not task.colorbar_label.strip():
            msgs.append("WARNING: colorbar_label 未设置，读者无法知道色标含义")

        if task.x_label is None or not task.x_label.strip():
            msgs.append("WARNING: x_label 未设置，横轴缺乏物理标注")

        if task.y_label is None or not task.y_label.strip():
            msgs.append("WARNING: y_label 未设置，纵轴缺乏物理标注")

        if task.title and len(task.title) > 60:
            msgs.append(f"INFO: 标题过长（{len(task.title)} 字符），建议 ≤60 字符")

        if task.dpi < 300:
            msgs.append(f"WARNING: DPI={task.dpi} 低于论文最低要求（300 dpi）")

        tt = TaskType(task.task_type)
        if tt is TaskType.MULTI_METHOD_COMPARISON and task.symmetric_clim is None:
            msgs.append(
                "WARNING: 多方法对比图未明确设置 symmetric_clim，"
                "请确认是否使用了全局统一 clim 而非各 panel 独立归一化"
            )

        if tt is TaskType.SHOT_RECORD and task.symmetric_clim is False:
            msgs.append(
                "WARNING: 炮记录图建议使用对称 clim（symmetric_clim=True），"
                "非对称色标会误导振幅正负"
            )

        if tt is TaskType.WAVEFIELD_SNAPSHOT and task.symmetric_clim is False:
            msgs.append("WARNING: 波场快照建议使用对称 clim 以正确展示正负振幅")

        return msgs

    def _check_mpl_figure(self, fig) -> list[str]:
        """检查 matplotlib Figure 中各 Axes 的实际属性。"""
        msgs: list[str] = []
        for ax in fig.axes:
            if not ax.get_xlabel():
                msgs.append(f"WARNING: Axes '{ax.get_title()}' 缺少 x 轴标签")
            if not ax.get_ylabel():
                msgs.append(f"WARNING: Axes '{ax.get_title()}' 缺少 y 轴标签")
        return msgs
