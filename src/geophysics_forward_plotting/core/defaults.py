"""Publication-oriented defaults used throughout the framework."""

DEFAULT_DPI = 600
DEFAULT_FIGURE_SIZE = (7.0, 4.5)
DEFAULT_EXPORT_FORMATS = ("png",)

# ── 统一字体 ──────────────────────────────────────────────────
# 论文标准: serif=Times New Roman (Geophysics/GJI/SEG 等期刊默认)
# 备选 sans-serif=Arial (Nature/Science), 中文=Noto Serif SC
DEFAULT_FONT_NAME = "serif"
DEFAULT_FONT_FAMILY_SERIF = ["Times New Roman", "STIXGeneral", "DejaVu Serif"]
DEFAULT_FONT_FAMILY_SANS = ["Arial", "Helvetica", "DejaVu Sans"]
DEFAULT_FONT_SIZE = 10.0          # 基准字号（tick / colorbar tick）
TITLE_FONT_SIZE = 13.0            # 子图标题
LABEL_FONT_SIZE = 11.0            # 坐标轴标签
COLORBAR_LABEL_FONT_SIZE = 11.0   # 色条标签
SUPTITLE_FONT_SIZE = 14.0         # 总标题
ANNOTATION_FONT_SIZE = 10.0       # 标注文字

DEFAULT_LINE_WIDTH = 1.0
DEFAULT_AXIS_LINE_WIDTH = 0.8

DEFAULT_DIVERGING_CMAP = "seismic"
DEFAULT_SEQUENTIAL_CMAP = "viridis"
DEFAULT_BACKGROUND_COLOR = "white"
SUPPORTED_EXPORT_FORMATS = frozenset({"png", "pdf", "svg"})

