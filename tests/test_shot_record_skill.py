"""测试 ShotRecordSkill。"""

import numpy as np
import pytest

from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.shot_record_skill import ShotRecordSkill


@pytest.fixture()
def shot_context():
    rng = np.random.default_rng(0)
    arr = rng.standard_normal((300, 120)).astype(np.float32)
    return DataContext(raw_data=(arr,))


def test_shot_record_uses_symmetric_clim(shot_context, tmp_path):
    skill = ShotRecordSkill()
    task = FigureTask(
        task_type="shot_record",
        output_dir=tmp_path,
        dt=0.002,
        dx=0.025,
        dpi=72,
        export_formats=("png",),
    )
    result = skill.run(task, shot_context)
    assert result.figure is not None
    assert result.saved_paths[0].exists()
