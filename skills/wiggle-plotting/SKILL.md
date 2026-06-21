---
name: wiggle-plotting
description: Plot seismic traces in wiggle / variable-area (wigb) style with skip, gain, and positive-fill controls, time axis down, and physical trace coordinates. Use when the user wants to show individual trace waveforms or a zoomed wiggle section of a gather rather than an image.
---

# Skill: wiggle-plotting

## Purpose

Plot seismic traces in wiggle (variable-area) style for localized trace comparison
or high-resolution display of individual receiver responses.

## When to Use

- You want to display individual seismic traces as waveforms (not as image).
- You need to compare waveform shape between methods at trace level.
- You are showing a zoomed-in section of a shot record with wiggle fill.
- You need `wigb`-style (wiggle with positive-fill) display.

## Inputs

| Parameter         | Type       | Description                                        |
|------------------|------------|----------------------------------------------------|
| `task_type`      | `"wiggle"` | Required                                           |
| `data_paths`     | list[str]  | Path to `.npy` array of shape `(nt, nx)`           |
| `dt`             | float      | Time sampling interval (s)                         |
| `dx`             | float      | Trace spacing (km)                                 |
| `x0`             | float      | X origin (km)                                      |
| `t0`             | float      | T origin (s)                                       |

Optional via `parameters`:
- `skip`: int — display every N-th trace (default 1)
- `gain`: float — amplitude scale factor (default 1.0)
- `fill_positive`: bool — fill positive lobe (wigb style, default True)

## Outputs

- `FigureResult.figure`: matplotlib Figure (wiggle traces)
- `FigureResult.saved_paths`: exported paths

## Geophysical Conventions

| Property       | Rule                                       |
|----------------|--------------------------------------------|
| X axis label   | `Offset (km)`                              |
| Y axis label   | `Time (s)`                                 |
| Y direction    | **Downward** (time=0 at top)               |
| Fill mode      | Positive-fill (wigb style) by default      |
| Figure size    | 1.5 column: 5.5 × 4.0 in                  |
| Font           | Times New Roman (serif), tick=10pt, label=11pt |
| DPI            | 600                                        |
| Export         | PDF (vector) + PNG (preview)               |

## Critical Rules

1. **Time axis MUST point downward** — `ax.invert_yaxis()` must be applied.
2. **Physical x coordinates** (km), not trace index.
3. Gain should be chosen so traces don't overlap excessively — typical: 1–3×.
4. `fill_positive=True` fills positive lobes in black (standard wigb style).

## Common Mistakes to Avoid

- Time axis pointing upward.
- Using array index instead of km for x axis.
- Gain too large causing overlapping traces.
- Missing `invert_yaxis()` call.

## Default Behavior

- skip: 1 (show all traces)
- gain: 1.0
- fill_positive: True
- DPI: 600

## Example Prompt

```
Plot seismic traces from shot_record.npy as wiggle display.
Shape (nt=300, nx=120). dt=0.002 s, dx=0.025 km.
Show every 2nd trace (skip=2), gain=1.5, fill positive lobes.
X axis: Receiver position (km). Y axis: Time (s), downward.
Export as PNG (600 dpi).
```
