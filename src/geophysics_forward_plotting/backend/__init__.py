"""Backend 子包：CIGVis 封装、Matplotlib 补充、参数适配层。"""

from geophysics_forward_plotting.backend import cigvis_backend, matplotlib_backend
from geophysics_forward_plotting.backend.cigvis_backend import is_available as cigvis_available

__all__ = ["cigvis_available", "cigvis_backend", "matplotlib_backend"]

