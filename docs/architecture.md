# Architecture

## Overview

```
geophysics-forward-plotting
│
├── PlottingAgent          ← 主入口：接收任务、路由、执行、审查
│   ├── TaskRouter         ← 按 task_type 定位技能
│   ├── Planner            ← YAML/dict → FigureTask
│   └── ReviewPipeline     ← 后处理规范检查
│
├── SkillRegistry          ← 注册和管理所有技能
│
├── Skills（执行层）
│   ├── DataInspectorSkill
│   ├── VelocityModelSkill
│   ├── ShotRecordSkill
│   ├── WavefieldSnapshotSkill
│   ├── MultiMethodCompareSkill
│   ├── WiggleSkill
│   ├── ErrorMapSkill
│   ├── PerformanceSkill
│   ├── Volume3DSkill
│   ├── SliceViewerSkill
│   ├── StyleSkill
│   ├── FigureReviewSkill
│   └── ExportSkill
│
├── Backend（渲染层）
│   ├── CigvisBackend      ← cigvis 封装（2D / 3D / SliceViewer）
│   ├── MatplotlibBackend  ← 统计图 / fallback
│   └── Adapters           ← FigureTask → backend 参数转换
│
└── Core（领域模型）
    ├── FigureTask         ← 用户请求的规范化表示
    ├── DataContext        ← 数组 + 物理元数据
    ├── FigureResult       ← 图件 + 保存路径 + 审查消息
    ├── PlotStyle          ← 论文风格参数
    ├── Conventions        ← 地球物理绘图约定
    └── Enums / Exceptions
```

## CigvisBackend 设计

## Data I/O Boundary

`core.io.load_array_with_metadata` is the single file-loading boundary used by
the Agent and CLI. It supports NPY, explicit-layout BIN, SEG-Y, and SU. SEG-Y/SU
are read with `segyio`, normalized to `(samples, traces)` by default, and retain
trace count, sample count, sample coordinates, and sample interval metadata.
DataInspector owns loading so metadata is not discarded by an earlier CLI step.

Raw binary shape, dtype, endianness, order, and offset are configuration, not
heuristics. Three-dimensional SEG-Y reshaping also requires a verified explicit
shape because flattened trace order alone does not prove inline/crossline geometry.

### 封装原则

`cigvis_backend.py` **不复制 CIGVis 内部实现**，只做接口适配：

1. 将 `FigureTask` / `DataContext` 转换为 cigvis 所需的参数格式。
2. 将框架的 `(nt/nz, nx)` 2D 契约适配到 CIGVis 的全局
   `LINE_FIRST` 设置，并在调用后恢复原设置。
3. 将 `(nz, ny, nx)` 体数据和切片索引统一转换为 CIGVis
   `(x, y, z/time)`，overlay 使用同一转换。
4. 处理 CIGVis API 在不同版本间的差异（集中维护）。
5. 提供 `is_available()` 检查，使上层 Skills 可安全降级。

### 任务分工

| 任务类型                | 优先 backend     | Fallback              |
|------------------------|------------------|-----------------------|
| 2D image (速度模型等)   | `cigvis.plot2d` | matplotlib imshow     |
| 1D seismogram / wiggle | `plot1d` / `plot_multi_traces` | matplotlib |
| 3D volume 渲染          | `create_slices` + `plot3D` | BackendUnavailableError|
| 浏览器 3D              | `cigvis.viserplot` | BackendUnavailableError|
| SliceViewer            | `create_slice` + `show` | BackendUnavailableError|
| 性能图 / 统计图         | matplotlib       | —（无 fallback 需要）  |

### Fallback 策略

- **2D 图件**：cigvis 不可用时自动 fallback 到 matplotlib（`_mpl_plot2d`）。
- **性能图**：默认使用 matplotlib，不依赖 cigvis。
- **3D / SliceViewer**：cigvis 不可用时**抛出 `BackendUnavailableError`**，给出清晰的安装提示，不静默失败。
- **CIGVis 已安装但 API 调用错误**：抛出 `BackendRenderError`，不把参数错误
  伪装成 matplotlib fallback。

### 数据方向边界

| 领域布局 | backend 输入 | CIGVis 实际输入 |
|---|---|---|
| 炮记录 | `(nt, nx)` | 2D 保持 `(nt, nx)`，关闭 CIGVis 自动转置 |
| 速度/波场 | `(nz, nx)` | 2D 保持 `(nz, nx)`，关闭 CIGVis 自动转置 |
| 3D 正演体 | `(nz, ny, nx)` | 转为 `(nx, ny, nz)` |
| CIGVis 原生体 | `(nx, ny, nz)` | 保持不变 |

SliceViewer 是维度通用 API，不做 3D 转置；对 `(nz, ny, nx)` 使用
`display_axes=(0, 2)` 显示“深度-距离”切片。

## CIGVis Gallery 参考

本项目所有 2D/3D 图件能力优先参考 CIGVis 已有实现：

- 2D 图件：https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-image
- 1D 地震道：https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-trace
- 3D 体数据：https://cigvis.readthedocs.io/en/latest/gallery/index.html#d-seismic-volume
- SliceViewer：https://cigvis.readthedocs.io/en/latest/gallery/index.html#sliceviewer
- Colormap：https://cigvis.readthedocs.io/en/latest/gallery/index.html#colormap

## 数据流

```
用户调用 PlottingAgent.run(task, context)
  ↓
TaskRouter.route(task)
  → 在 SkillRegistry 中查找匹配 skill
  ↓
skill.run(task, context)
  → 调用 CigvisBackend 或 MatplotlibBackend
  → 返回 FigureResult
  ↓
skill.review(result)    ← skill 内部检查
  ↓
ReviewPipeline.run_review(task, result)  ← 全局规范检查
  ↓
FigureResult（含 figure + saved_paths + review_messages）
```

## 扩展方式

新增一个绘图 Skill 只需要：

1. 继承 `BaseSkill`，实现 `can_handle` 和 `run`。
2. 在 `PlottingAgent._build_default_registry()` 中注册。
3. 在 `skills/<name>/SKILL.md` 中添加技能说明。
4. 可选：在 `examples/configs/` 和 `examples/scripts/` 中添加示例。
