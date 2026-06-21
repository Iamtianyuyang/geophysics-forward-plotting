"""技能子包：所有可执行绘图技能和注册表。"""

from geophysics_forward_plotting.skills.base import BaseSkill
from geophysics_forward_plotting.skills.data_inspector_skill import DataInspectorSkill
from geophysics_forward_plotting.skills.error_map_skill import ErrorMapSkill
from geophysics_forward_plotting.skills.export_skill import ExportSkill
from geophysics_forward_plotting.skills.figure_review_skill import FigureReviewSkill
from geophysics_forward_plotting.skills.multi_method_compare_skill import MultiMethodCompareSkill
from geophysics_forward_plotting.skills.performance_skill import PerformanceSkill
from geophysics_forward_plotting.skills.registry import SkillRegistry
from geophysics_forward_plotting.skills.shot_record_skill import ShotRecordSkill
from geophysics_forward_plotting.skills.sliceviewer_skill import SliceViewerSkill
from geophysics_forward_plotting.skills.style_skill import StyleSkill
from geophysics_forward_plotting.skills.velocity_model_skill import VelocityModelSkill
from geophysics_forward_plotting.skills.volume_3d_skill import Volume3DSkill
from geophysics_forward_plotting.skills.wavefield_snapshot_skill import WavefieldSnapshotSkill
from geophysics_forward_plotting.skills.wiggle_skill import WiggleSkill

__all__ = [
    "BaseSkill",
    "DataInspectorSkill",
    "ErrorMapSkill",
    "ExportSkill",
    "FigureReviewSkill",
    "MultiMethodCompareSkill",
    "PerformanceSkill",
    "SkillRegistry",
    "ShotRecordSkill",
    "SliceViewerSkill",
    "StyleSkill",
    "VelocityModelSkill",
    "Volume3DSkill",
    "WavefieldSnapshotSkill",
    "WiggleSkill",
]

