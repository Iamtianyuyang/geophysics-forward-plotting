"""测试 WiggleSkill。"""

import numpy as np

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.wiggle_skill import WiggleSkill


def test_wiggle_basic(tmp_path):
    rng = np.random.default_rng(3)
    arr = rng.standard_normal((200, 40)).astype(np.float32)
    ctx = DataContext(raw_data=(arr,))

    skill = WiggleSkill()
    task = FigureTask(
        task_type="wiggle",
        output_dir=tmp_path,
        dt=0.002,
        dx=0.025,
        dpi=72,
        export_formats=("png",),
        parameters={"skip": 4, "gain": 1.5},
    )
    result = skill.run(task, ctx)
    assert result.figure is not None
    assert result.saved_paths[0].exists()


def test_wiggle_prefers_cigvis_backend(monkeypatch, tmp_path):
    called = False

    def fake_plot(data, **kwargs):
        nonlocal called
        called = True
        from geophysics_forward_plotting.backend.matplotlib_backend import wiggle_plot

        kwargs.pop("scale", None)
        return wiggle_plot(data, **kwargs)

    monkeypatch.setattr(cigvis_backend, "plot1d_wiggle", fake_plot)
    data = np.ones((20, 5), dtype=np.float32)
    task = FigureTask(
        task_type="wiggle",
        output_dir=tmp_path,
        dt=0.002,
        dx=0.025,
        dpi=72,
        export_formats=("png",),
    )

    WiggleSkill().run(task, DataContext(raw_data=(data,)))

    assert called
