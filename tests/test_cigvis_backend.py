from __future__ import annotations

from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np

from geophysics_forward_plotting.backend import adapters, cigvis_backend
from geophysics_forward_plotting.core.enums import DataLayout


class FakeCigvis2D:
    def __init__(self) -> None:
        self.line_first = True

    def is_line_first(self) -> bool:
        return self.line_first

    def set_order(self, line_first: bool) -> None:
        self.line_first = line_first

    def plot2d(self, data, *, ax, cmap, clim, **kwargs) -> None:
        rendered = data.T if self.line_first else data
        ax.imshow(rendered, cmap=cmap, vmin=clim[0], vmax=clim[1], aspect="auto")


def test_cigvis_plot2d_preserves_vertical_first_shape(monkeypatch) -> None:
    fake = FakeCigvis2D()
    monkeypatch.setattr(cigvis_backend, "cigvis", fake)
    monkeypatch.setattr(cigvis_backend, "_CIGVIS_AVAILABLE", True)
    data = np.arange(6, dtype=float).reshape(2, 3)

    fig = cigvis_backend.plot2d_image(
        data,
        clim=(0.0, 5.0),
        xsample=np.array([10.0, 10.5, 11.0]),
        ysample=np.array([1.0, 1.2]),
    )

    ax = fig.axes[0]
    assert ax.images[0].get_array().shape == data.shape
    assert ax.get_ylim()[0] > ax.get_ylim()[1]
    assert fake.line_first is True
    plt.close(fig)


def test_nz_ny_nx_volume_is_adapted_to_cigvis_xyz() -> None:
    volume = np.arange(2 * 3 * 4).reshape(2, 3, 4)

    adapted = adapters.to_cigvis_volume(volume, DataLayout.NZ_NY_NX)

    assert adapted.shape == (4, 3, 2)
    np.testing.assert_array_equal(adapted[:, :, 0], volume[0].T)


def test_sliceviewer_uses_create_slice_api(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    class FakeSliceViewer:
        @staticmethod
        def create_slice(volume, **kwargs):
            calls.append(("create_slice", kwargs))
            return [SimpleNamespace(volume=volume, kwargs=kwargs)]

        @staticmethod
        def show(nodes, **kwargs):
            calls.append(("show", kwargs))
            return "server"

    monkeypatch.setattr(
        cigvis_backend,
        "cigvis",
        SimpleNamespace(sliceviewer=FakeSliceViewer),
    )
    monkeypatch.setattr(cigvis_backend, "_CIGVIS_AVAILABLE", True)
    volume = np.zeros((4, 5, 6), dtype=np.float32)

    result = cigvis_backend.launch_sliceviewer(
        volume,
        display_axes=(0, 2),
        indices={1: 2},
        axis_labels=("Depth", "Crossline", "Distance"),
        show=False,
    )

    assert result.nodes[0].volume is volume
    assert result.server is None
    assert calls == [
        (
            "create_slice",
            {
                "display_axes": (0, 2),
                "indices": {1: 2},
                "axis_labels": ("Depth", "Crossline", "Distance"),
                "cmap": "gray",
                "clim": None,
                "aspect": "auto",
                "interpolation": "nearest",
                "render_mode": "float",
            },
        )
    ]


def test_plot3d_adapts_native_layout_and_slice_positions(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakeCigvis3D:
        def __init__(self) -> None:
            self.line_first = False

        def is_line_first(self) -> bool:
            return self.line_first

        def set_order(self, line_first: bool) -> None:
            self.line_first = line_first

        def create_slices(self, volume, **kwargs):
            calls["volume"] = volume
            calls["position"] = kwargs["pos"]
            calls["line_first_during_create"] = self.line_first
            return ["slice"]

        @staticmethod
        def create_colorbar_from_nodes(nodes, label, select):
            return ["colorbar"]

        @staticmethod
        def create_axis(shape, mode, **kwargs):
            calls["axis_shape"] = shape
            calls["axis_labels"] = kwargs["axis_labels"]
            return ["axis"]

        @staticmethod
        def Plot3DView(**kwargs):
            return kwargs

        @staticmethod
        def plot3D(nodes, **kwargs):
            calls["nodes"] = nodes
            return "canvas"

    fake = FakeCigvis3D()
    monkeypatch.setattr(cigvis_backend, "cigvis", fake)
    monkeypatch.setattr(cigvis_backend, "_CIGVIS_AVAILABLE", True)
    volume = np.arange(2 * 3 * 4).reshape(2, 3, 4)

    handle = cigvis_backend.plot3d_volume(
        volume,
        layout=DataLayout.NZ_NY_NX,
        slices=(1, 1, 2),
        view_kwargs={"show": False},
    )

    assert calls["volume"].shape == (4, 3, 2)
    assert calls["position"] == {"x": [2], "y": [1], "z": [1]}
    assert calls["axis_shape"] == (4, 3, 2)
    assert calls["line_first_during_create"] is True
    assert handle.nodes == ["slice", "colorbar", "axis"]
    assert fake.line_first is False
