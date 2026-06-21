---
name: figure-review
description: Review a figure task for geophysical convention compliance — checks colorbar/axis labels, DPI ≥ 300, symmetric color limits on amplitude data, and unified clim on multi-panel comparisons — returning warnings without modifying the figure. Runs automatically after every plot; invoke explicitly for a standalone pre-submission check.
---

# Skill: figure-review

## Purpose

Automatically review geophysical figures for convention compliance before submission.
Returns a list of warnings and suggestions — does not modify the figure.

## When to Use

- Before exporting a figure for a paper submission.
- When you want to verify that all geophysical plotting conventions are followed.
- When performing batch quality checks on multiple figures.

## What Is Checked

| Check                             | Severity | Description                                           |
|-----------------------------------|----------|-------------------------------------------------------|
| colorbar_label missing            | WARNING  | Colorbar must have a label describing the quantity    |
| x_label missing                   | WARNING  | X axis must have a label with units                   |
| y_label missing                   | WARNING  | Y axis must have a label with units                   |
| title too long                    | INFO     | Title > 60 chars may be truncated in papers           |
| DPI < 300                         | WARNING  | Publication requires DPI ≥ 300 (default 600)          |
| multi-method with no global clim  | WARNING  | Must confirm unified clim for comparison figures      |
| shot_record with symmetric=False  | WARNING  | Amplitude data must use symmetric clim                |
| wavefield with symmetric=False    | WARNING  | Wavefield amplitude must be symmetric                 |
| Axes missing xlabel/ylabel        | WARNING  | Each matplotlib Axes must have labeled axes           |
| Export format missing PDF         | INFO     | Vector PDF preferred for journal submission           |

### Typography and Sizing Checks (Paper Standards)

| Property       | Expected value                                    |
|----------------|---------------------------------------------------|
| Font family    | serif (Times New Roman)                           |
| Tick labelsize | 10 pt                                             |
| Axis label     | 11 pt                                             |
| Subplot title  | 13 pt                                             |
| Suptitle       | 14 pt                                             |
| DPI            | 600 (publication default)                         |
| Export         | PDF + PNG                                         |

### Figure Size Guidelines

| Layout         | Width (in) | Use when                              |
|----------------|------------|---------------------------------------|
| Single column  | 3.5        | Velocity, wavefield, performance      |
| 1.5 column     | 5.5        | Shot record, wiggle, error map        |
| Double column  | 7.0        | Multi-method comparison (2×2)         |

## Inputs

Any `FigureTask` — the reviewer checks the task configuration.
Optionally, a `FigureResult` with a matplotlib Figure for deeper inspection.

## Outputs

- `FigureResult.review_messages`: list of warning/info strings
- `FigureResult.summary`: "N 条提示" summary

## Integration

FigureReviewSkill runs automatically after every plotting skill in `PlottingAgent`
(controlled by `auto_review=True`, the default).
It can also be called explicitly:

```python
from geophysics_forward_plotting.agent.review import run_review
messages = run_review(task, result)
```

Or via CLI:
```bash
gfp review examples/configs/shot_record.yaml
```

## Geophysical Conventions

- Require physical axis labels with units for distance, depth, time, velocity, and performance.
- Require depth and time axes to increase downward for image-like seismic displays.
- Require symmetric color limits for signed amplitudes and signed errors.
- Require one global color limit and a shared colorbar for multi-method comparisons.
- Require explicit error definitions and performance baselines when applicable.

## Common Mistakes to Avoid

- Omitted colorbar labels (very common).
- Using DPI=72 (screen resolution) instead of 600 (publication).
- Forgetting to confirm unified clim in comparison figures.
- Non-symmetric clim in amplitude figures.

Do not treat a clean configuration review as proof that rendered labels, clipping,
or panel alignment are correct. Inspect the figure object when it is available.

## Default Behavior

- Run after every plotting skill when `PlottingAgent.auto_review` is enabled.
- Return warnings and information without mutating the task or figure.
- Use 300 dpi as the minimum raster threshold and 600 dpi as the export default.
- Escalate missing units, invalid amplitude scaling, and non-unified comparison limits.

## Example Prompt

```
Review the configuration for a shot record figure:
- task_type: shot_record
- colorbar_label: None (missing)
- dpi: 150

Expected output:
  WARNING: colorbar_label 未设置
  WARNING: DPI=150 低于论文最低要求（300 dpi）
```
