"""测试 DataInspectorSkill 的布局推断逻辑。"""


import numpy as np
import pytest

from geophysics_forward_plotting.core.enums import DataKind, DataLayout, TaskType
from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.data_inspector_skill import (
    DataInspectorSkill,
    _infer_layout,
)


def test_infer_layout_shot_record_nt_nx():
    # nt > nx → (nt, nx)
    layout = _infer_layout((300, 120), TaskType.SHOT_RECORD)
    assert layout == DataLayout.NT_NX


def test_infer_layout_shot_record_nx_nt():
    # nx > nt → (nx, nt)
    layout = _infer_layout((120, 300), TaskType.SHOT_RECORD)
    assert layout == DataLayout.NX_NT


def test_infer_layout_velocity_model():
    layout = _infer_layout((60, 120), TaskType.VELOCITY_MODEL)
    assert layout == DataLayout.NZ_NX


def test_infer_layout_3d():
    layout = _infer_layout((30, 30, 60), TaskType.VOLUME_3D)
    assert layout == DataLayout.NZ_NY_NX


def test_data_inspector_no_paths(tmp_path):
    skill = DataInspectorSkill()
    task = FigureTask(task_type="velocity_model", data_paths=())
    result = skill.run(task, DataContext())
    assert "无数据路径" in result.summary


def test_data_inspector_loads_npy(tmp_path):
    arr = np.ones((60, 120), dtype=np.float32) * 2000.0
    npy = tmp_path / "vel.npy"
    np.save(npy, arr)

    skill = DataInspectorSkill()
    task = FigureTask(task_type="velocity_model", data_paths=(str(npy),))
    result = skill.run(task, DataContext())

    ctx = result.metadata["context"]
    assert ctx.shape == (60, 120)
    assert ctx.data_kind == DataKind.VELOCITY
    assert ctx.value_range == pytest.approx((2000.0, 2000.0))
