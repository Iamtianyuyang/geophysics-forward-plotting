from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from geophysics_forward_plotting.backend.adapters import (
    build_imshow_kwargs,
    build_wiggle_kwargs,
)
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.io import load_array, load_array_with_metadata
from geophysics_forward_plotting.core.models import DataContext, FigureTask, PlotStyle


def test_load_binary_with_explicit_shape_and_big_endian(tmp_path) -> None:
    expected = np.arange(12, dtype=np.float32).reshape(3, 4)
    path = tmp_path / "shot.bin"
    expected.astype(">f4").tofile(path)

    loaded = load_array_with_metadata(
        path,
        {"shape": [3, 4], "dtype": "float32", "endianness": "big"},
    )

    np.testing.assert_array_equal(loaded.data, expected)
    assert loaded.metadata["format"] == "bin"
    assert loaded.metadata["endianness"] == "big"


def test_binary_requires_shape(tmp_path) -> None:
    path = tmp_path / "unknown.bin"
    np.arange(4, dtype=np.float32).tofile(path)

    with pytest.raises(DataValidationError, match="requires data_options.shape"):
        load_array(path)


class _FakeRaw:
    def __init__(self, traces: np.ndarray) -> None:
        self.traces = traces

    def __getitem__(self, _key):
        return self.traces


class _FakeSeismic:
    def __init__(self, traces: np.ndarray) -> None:
        self.trace = SimpleNamespace(raw=_FakeRaw(traces))
        self.samples = np.arange(traces.shape[1], dtype=float) * 2.0
        self.mapped = False

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def mmap(self) -> None:
        self.mapped = True


@pytest.fixture
def fake_segyio(monkeypatch):
    calls: list[tuple[str, dict]] = []
    traces = np.arange(12, dtype=np.float32).reshape(3, 4)

    def open_segy(_path, **kwargs):
        calls.append(("segy", kwargs))
        return _FakeSeismic(traces)

    def open_su(_path, **kwargs):
        calls.append(("su", kwargs))
        return _FakeSeismic(traces)

    module = SimpleNamespace(
        open=open_segy,
        su=SimpleNamespace(open=open_su),
        tools=SimpleNamespace(dt=lambda _file, fallback_dt=0.0: 2000.0),
    )
    monkeypatch.setitem(sys.modules, "segyio", module)
    return traces, calls


def test_load_segy_transposes_to_samples_traces_and_reads_dt(
    tmp_path,
    fake_segyio,
) -> None:
    traces, calls = fake_segyio
    path = tmp_path / "shot.segy"
    path.write_bytes(b"fake")

    loaded = load_array_with_metadata(path)

    np.testing.assert_array_equal(loaded.data, traces.T)
    assert loaded.metadata["data_layout"] == "nt_nx"
    assert loaded.metadata["sample_interval_s"] == pytest.approx(0.002)
    assert loaded.metadata["trace_count"] == 3
    assert calls[0][0] == "segy"


def test_load_su_can_preserve_trace_major_layout(tmp_path, fake_segyio) -> None:
    traces, calls = fake_segyio
    path = tmp_path / "shot.su"
    path.write_bytes(b"fake")

    loaded = load_array_with_metadata(path, {"output_layout": "traces_samples"})

    np.testing.assert_array_equal(loaded.data, traces)
    assert loaded.metadata["data_layout"] == "nx_nt"
    assert calls[0][0] == "su"


def test_load_segy_can_reshape_volume(tmp_path, fake_segyio) -> None:
    _traces, _calls = fake_segyio
    path = tmp_path / "volume.sgy"
    path.write_bytes(b"fake")

    loaded = load_array_with_metadata(path, {"shape": [4, 1, 3]})

    assert loaded.data.shape == (4, 1, 3)
    assert loaded.metadata["data_layout"] == "nz_ny_nx"


def test_seismic_header_dt_is_used_for_image_and_wiggle_axes() -> None:
    context = DataContext(
        raw_data=(np.zeros((4, 3), dtype=np.float32),),
        metadata={"sample_interval_s": 0.004},
    )
    task = FigureTask(task_type="shot_record")

    image_kwargs = build_imshow_kwargs(task, context, PlotStyle())
    wiggle_kwargs = build_wiggle_kwargs(task, PlotStyle(), context)

    np.testing.assert_allclose(image_kwargs["ysample"], [0.0, 0.004, 0.008, 0.012])
    assert wiggle_kwargs["dt"] == pytest.approx(0.004)
