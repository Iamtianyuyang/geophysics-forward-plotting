from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from geophysics_forward_plotting.core.models import FigureResult
from geophysics_forward_plotting.skills.figure_review_skill import FigureReviewSkill


def test_review_detects_transpose_upward_axis_and_independent_clim() -> None:
    fig, axes = plt.subplots(1, 2)
    axes[0].imshow(np.zeros((3, 2)), vmin=-1.0, vmax=1.0)
    axes[1].imshow(np.zeros((2, 3)), vmin=-2.0, vmax=2.0)
    for axis in axes:
        axis.set_xlabel("Distance (km)")
        axis.set_ylabel("Depth (km)")
    axes[0].set_ylim(0.0, 3.0)

    result = FigureResult(
        figure=fig,
        metadata={
            "expected_image_shapes": [(2, 3), (2, 3)],
            "expected_y_direction": "down",
            "shared_clim": True,
        },
    )
    messages = FigureReviewSkill().review(result)

    assert any("may be transposed" in message for message in messages)
    assert any("vertical axis is not downward" in message for message in messages)
    assert any("one shared color limit" in message for message in messages)
    plt.close(fig)


def test_review_accepts_correct_image_shape_and_direction() -> None:
    fig, axis = plt.subplots()
    image = axis.imshow(np.zeros((2, 3)), origin="upper")
    fig.colorbar(image, ax=axis, label="Amplitude")
    axis.set_xlabel("Distance (km)")
    axis.set_ylabel("Time (s)")
    result = FigureResult(
        figure=fig,
        metadata={
            "expected_image_shapes": [(2, 3)],
            "expected_y_direction": "down",
        },
    )

    assert FigureReviewSkill().review(result) == []
    plt.close(fig)
