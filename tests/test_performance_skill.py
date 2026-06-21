"""测试 PerformanceSkill（单系列和多系列）。"""

import pytest

from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.performance_skill import PerformanceSkill


def test_single_series(tmp_path):
    skill = PerformanceSkill()
    task = FigureTask(
        task_type="performance",
        output_dir=tmp_path,
        dpi=72,
        export_formats=("png",),
        parameters={
            "categories": ["A", "B", "C"],
            "values": [1.0, 2.5, 4.0],
            "metric_label": "Time (s)",
        },
    )
    result = skill.run(task, DataContext())
    assert result.figure is not None
    assert result.saved_paths[0].exists()


def test_multi_series(tmp_path):
    skill = PerformanceSkill()
    task = FigureTask(
        task_type="performance",
        output_dir=tmp_path,
        dpi=72,
        export_formats=("png",),
        parameters={
            "categories": ["Small", "Medium", "Large"],
            "series": {"FD": [1, 4, 9], "RTM": [2, 6, 15]},
            "metric_label": "Time (s)",
        },
    )
    result = skill.run(task, DataContext())
    assert result.figure is not None


def test_missing_data_raises(tmp_path):
    skill = PerformanceSkill()
    task = FigureTask(task_type="performance", output_dir=tmp_path, dpi=72)
    with pytest.raises(DataValidationError):
        skill.run(task, DataContext())
