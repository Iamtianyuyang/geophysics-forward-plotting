"""测试 MultiMethodCompareSkill（统一 clim）。"""

import numpy as np
import pytest

from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.multi_method_compare_skill import MultiMethodCompareSkill


@pytest.fixture()
def compare_context():
    rng = np.random.default_rng(1)
    arrays = tuple(rng.standard_normal((60, 120)).astype(np.float32) for _ in range(4))
    return DataContext(raw_data=arrays)


def test_compare_4_methods(compare_context, tmp_path):
    skill = MultiMethodCompareSkill()
    task = FigureTask(
        task_type="multi_method_comparison",
        output_dir=tmp_path,
        method_names=("A", "B", "C", "D"),
        dx=0.025,
        dz=0.025,
        symmetric_clim=True,
        dpi=72,
        export_formats=("png",),
    )
    result = skill.run(task, compare_context)
    assert result.figure is not None
    assert result.saved_paths[0].exists()


def test_compare_rejects_too_many_methods(tmp_path):
    rng = np.random.default_rng(2)
    arrays = tuple(rng.standard_normal((10, 10)).astype(np.float32) for _ in range(5))
    ctx = DataContext(raw_data=arrays)
    skill = MultiMethodCompareSkill()
    task = FigureTask(
        task_type="multi_method_comparison",
        output_dir=tmp_path,
        dpi=72,
    )
    from geophysics_forward_plotting.core.exceptions import DataValidationError
    with pytest.raises(DataValidationError, match="最多支持 4"):
        skill.run(task, ctx)
