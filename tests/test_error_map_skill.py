"""测试 ErrorMapSkill 的三种误差模式。"""

import numpy as np
import pytest

from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.error_map_skill import ErrorMapSkill


@pytest.fixture()
def two_arrays():
    rng = np.random.default_rng(4)
    pred = rng.standard_normal((60, 120)).astype(np.float32)
    ref = pred + rng.standard_normal((60, 120)).astype(np.float32) * 0.1
    return DataContext(raw_data=(pred, ref))


@pytest.mark.parametrize("mode", ["signed", "absolute", "relative"])
def test_error_modes(two_arrays, tmp_path, mode):
    skill = ErrorMapSkill()
    task = FigureTask(
        task_type="error_map",
        output_dir=tmp_path,
        dx=0.025,
        dz=0.025,
        dpi=72,
        export_formats=("png",),
        parameters={"error_mode": mode},
    )
    result = skill.run(task, two_arrays)
    assert result.figure is not None
    assert result.saved_paths[0].exists()


def test_error_map_needs_two_arrays(tmp_path):
    rng = np.random.default_rng(5)
    ctx = DataContext(raw_data=(rng.standard_normal((10, 10)).astype(np.float32),))
    skill = ErrorMapSkill()
    task = FigureTask(task_type="error_map", output_dir=tmp_path, dpi=72)
    with pytest.raises(DataValidationError):
        skill.run(task, ctx)
