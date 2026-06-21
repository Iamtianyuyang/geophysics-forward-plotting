from __future__ import annotations

import numpy as np

from geophysics_forward_plotting.backend import cigvis_backend
from geophysics_forward_plotting.core.enums import DataLayout
from geophysics_forward_plotting.core.models import DataContext, FigureTask
from geophysics_forward_plotting.skills.sliceviewer_skill import SliceViewerSkill
from geophysics_forward_plotting.skills.volume_3d_skill import Volume3DSkill


def test_volume_skill_passes_explicit_layout_and_engine(monkeypatch) -> None:
    captured = {}

    def fake_plot3d(data, **kwargs):
        captured["shape"] = data.shape
        captured.update(kwargs)
        return cigvis_backend.Volume3DHandle(nodes=[], engine=kwargs["engine"])

    monkeypatch.setattr(cigvis_backend, "is_available", lambda: True)
    monkeypatch.setattr(cigvis_backend, "plot3d_volume", fake_plot3d)
    context = DataContext(
        raw_data=(np.zeros((2, 3, 4), dtype=np.float32),),
        inferred_layout=DataLayout.NZ_NY_NX,
    )
    task = FigureTask(
        task_type="volume_3d",
        export_formats=(),
        parameters={"data_layout": "nz_ny_nx", "engine": "vispy"},
    )

    result = Volume3DSkill().run(task, context)

    assert captured["shape"] == (2, 3, 4)
    assert captured["layout"] is DataLayout.NZ_NY_NX
    assert captured["engine"] == "vispy"
    assert result.metadata == {"data_layout": "nz_ny_nx", "engine": "vispy"}


def test_sliceviewer_skill_uses_native_nz_ny_nx_display_axes(monkeypatch) -> None:
    captured = {}

    def fake_launch(data, **kwargs):
        captured["data"] = data
        captured.update(kwargs)
        return cigvis_backend.SliceViewerHandle(nodes=["slice"])

    monkeypatch.setattr(cigvis_backend, "is_available", lambda: True)
    monkeypatch.setattr(cigvis_backend, "launch_sliceviewer", fake_launch)
    volume = np.zeros((2, 3, 4), dtype=np.float32)
    context = DataContext(
        raw_data=(volume,),
        inferred_layout=DataLayout.NZ_NY_NX,
    )
    task = FigureTask(
        task_type="sliceviewer",
        export_formats=(),
        parameters={"data_layout": "nz_ny_nx", "show": False},
    )

    result = SliceViewerSkill().run(task, context)

    assert captured["data"] is volume
    assert captured["display_axes"] == (0, 2)
    assert captured["axis_labels"] == ("Depth", "Crossline", "Distance")
    assert captured["show"] is False
    assert result.metadata["display_axes"] == (0, 2)
