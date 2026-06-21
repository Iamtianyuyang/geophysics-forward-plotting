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

### 封装原则

`cigvis_backend.py` **不复制 CIGVis 内部实现**，只做接口适配：

1. 将 `FigureTask` / `DataContext` 转换为 cigvis 所需的参数格式。
2. 处理 cigvis API 在不同版本间的差异（集中维护）。
3. 提供 `is_available()` 检查，使上层 Skills 可安全降级。

### 任务分工

| 任务类型                | 优先 backend     | Fallback              |
|------------------------|------------------|-----------------------|
| 2D image (速度模型等)   | cigvis.mpl.plot2d| matplotlib imshow     |
| 1D seismogram / wiggle | cigvis 1D trace  | matplotlib            |
| 3D volume 渲染          | cigvis.plot3d    | BackendUnavailableError|
| SliceViewer            | cigvis.SliceViewer| BackendUnavailableError|
| 性能图 / 统计图         | matplotlib       | —（无 fallback 需要）  |

### Fallback 策略

- **2D 图件**：cigvis 不可用时自动 fallback 到 matplotlib（`_mpl_plot2d`）。
- **性能图**：默认使用 matplotlib，不依赖 cigvis。
- **3D / SliceViewer**：cigvis 不可用时**抛出 `BackendUnavailableError`**，给出清晰的安装提示，不静默失败。

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
