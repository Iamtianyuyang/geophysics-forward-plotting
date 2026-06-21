"""测试 VelocityModelSkill 的基本执行流程。"""

import numpy as np
import pytest

from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.velocity_model_skill import VelocityModelSkill


@pytest.fixture()
def vel_context():
    arr = np.linspace(1500, 4000, 60 * 120).reshape(60, 120).astype(np.float32)
    return DataContext(raw_data=(arr,))


def test_can_handle():
    skill = VelocityModelSkill()
    task = FigureTask(task_type="velocity_model")
    assert skill.can_handle(task)
    task2 = FigureTask(task_type="shot_record")
    assert not skill.can_handle(task2)


def test_run_produces_figure(vel_context, tmp_path):
    skill = VelocityModelSkill()
    task = FigureTask(
        task_type="velocity_model",
        output_dir=tmp_path,
        dx=0.025,
        dz=0.025,
        dpi=72,  # 测试用低 dpi
        export_formats=("png",),
    )
    result = skill.run(task, vel_context)
    assert result.figure is not None
    assert len(result.saved_paths) == 1
    assert result.saved_paths[0].suffix == ".png"
    assert result.saved_paths[0].exists()
