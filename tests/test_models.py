from pathlib import Path

import numpy as np
import pytest

from geophysics_forward_plotting.core.enums import AxisDirection, TaskType
from geophysics_forward_plotting.core.exceptions import ConfigurationError
from geophysics_forward_plotting.core.models import FigureTask, PhysicalAxis


def test_figure_task_normalizes_values() -> None:
    task = FigureTask(
        task_type="shot_record",
        data_paths=["shot.npy"],
        export_formats=[".PNG", "pdf"],
    )

    assert task.task_type is TaskType.SHOT_RECORD
    assert task.data_paths == (Path("shot.npy"),)
    assert task.export_formats == ("png", "pdf")


def test_figure_task_rejects_invalid_sampling() -> None:
    with pytest.raises(ConfigurationError, match="dt must be positive"):
        FigureTask(task_type=TaskType.SHOT_RECORD, dt=0.0)


def test_physical_axis_generates_coordinates() -> None:
    axis = PhysicalAxis(
        name="time",
        label="Time",
        unit="s",
        sampling=0.004,
        origin=0.1,
        size=3,
        direction=AxisDirection.DOWNWARD,
    )

    np.testing.assert_allclose(axis.coordinates(), [0.1, 0.104, 0.108])
    assert axis.display_label == "Time (s)"

