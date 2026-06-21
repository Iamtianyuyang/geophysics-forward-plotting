# Quick Start

## Connect an AI coding tool

Validate the canonical catalog and install project-local copies for the tools you use:

```bash
gfp agent-skills validate
gfp agent-skills install --tool codex claude cursor
```

The repository also includes `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules,
and GitHub Copilot instructions. See [Agent Skills Integration](agent-skills.md).

## Installation

```bash
conda env create -f environment.yml
conda activate geophysics-forward-plotting
```

To add matplotlib for plotting (if not already in environment):
```bash
conda install matplotlib
```

To add cigvis for 3D visualization:
```bash
pip install cigvis
```

## Generate Example Data

```bash
gfp data examples/data
```

## Python API

### Velocity Model

```python
from pathlib import Path
import numpy as np
from geophysics_forward_plotting import FigureTask, PlottingAgent
from geophysics_forward_plotting.core.models import DataContext

data = np.load("examples/data/velocity_model.npy")
context = DataContext(raw_data=(data,))

task = FigureTask(
    task_type="velocity_model",
    title="Velocity Model",
    output_dir=Path("examples/outputs"),
    dx=0.025,    # km
    dz=0.025,    # km
    x_label="Distance (km)",
    y_label="Depth (km)",
    colorbar_label="Velocity (m/s)",
    export_formats=("png", "pdf"),
    dpi=600,
)

agent = PlottingAgent()
result = agent.run(task, context)

for path in result.saved_paths:
    print(path)
```

### Shot Record

```python
task = FigureTask(
    task_type="shot_record",
    output_dir=Path("examples/outputs"),
    dt=0.002,
    dx=0.025,
    x_label="Receiver position (km)",
    y_label="Time (s)",
    colorbar_label="Amplitude",
    symmetric_clim=True,   # REQUIRED for amplitude
    export_formats=("png",),
    dpi=600,
)
```

### Four-Method Comparison

```python
import numpy as np
from geophysics_forward_plotting.core.models import DataContext

arrays = tuple(np.load(f"examples/data/method_{c}.npy") for c in "abcd")
context = DataContext(raw_data=arrays)

task = FigureTask(
    task_type="multi_method_comparison",
    method_names=("FD", "RTM", "LSRTM", "FWI"),
    symmetric_clim=True,     # MUST use unified global clim
    colorbar_label="Amplitude",
    export_formats=("png", "pdf"),
    dpi=600,
)
```

## CLI

```bash
# 渲染图件
gfp render examples/configs/velocity_model.yaml

# 查看任务计划（不渲染）
gfp plan examples/configs/shot_record.yaml

# 检查配置规范
gfp review examples/configs/compare_4methods.yaml

# 列出所有技能
gfp skills

# 生成示例数据
gfp data examples/data
```

## Run Example Scripts

```bash
python examples/scripts/demo_velocity_model.py
python examples/scripts/demo_shot_record.py
python examples/scripts/demo_compare_4methods.py
python examples/scripts/demo_performance.py
```

## Run Tests

```bash
pytest tests/ -v
```
