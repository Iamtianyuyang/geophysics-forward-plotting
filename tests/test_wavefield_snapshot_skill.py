"""测试 WavefieldSnapshotSkill。"""

import numpy as np
import pytest

from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.wavefield_snapshot_skill import WavefieldSnapshotSkill


@pytest.fixture()
def snap_context():
    zz, xx = np.mgrid[0:60, 0:120]
    arr = np.sin(0.3 * xx) * np.cos(0.2 * zz)
    return DataContext(raw_data=(arr.astype(np.float32),))


def test_snapshot_with_time_annotation(snap_context, tmp_path):
    skill = WavefieldSnapshotSkill()
    task = FigureTask(
        task_type="wavefield_snapshot",
        output_dir=tmp_path,
        dx=0.025,
        dz=0.025,
        dpi=72,
        export_formats=("png",),
        parameters={"snapshot_time": 0.25},
    )
    result = skill.run(task, snap_context)
    assert result.figure is not None
    assert result.saved_paths[0].exists()
