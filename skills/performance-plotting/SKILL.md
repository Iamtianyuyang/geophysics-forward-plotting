---
name: performance-plotting
description: Plot a bar or line chart comparing computational performance (wall-clock time, memory, speedup) across methods or grid sizes, with mandatory metric units and a named baseline. Use when the user wants a benchmark or efficiency figure; data is passed via task parameters, not .npy files.
---

# Skill: performance-plotting

## Purpose

Plot computational performance comparisons (time, memory, speedup) between methods.
These figures appear in the "Computational Efficiency" sections of geophysical papers.

## When to Use

- You need to compare wall-clock time across methods.
- You need to compare memory consumption.
- You need to show speedup ratios relative to a baseline.
- You are generating a Figure or Table supplement on efficiency.

## Inputs

| Parameter         | Type             | Description                                          |
|------------------|------------------|------------------------------------------------------|
| `task_type`      | `"performance"`  | Required                                             |
| `method_names`   | list[str]        | Names of methods being compared                      |

Data via `parameters` dict (not `.npy` files):

Single-series mode:
- `parameters["categories"]`: list[str] — method or problem-size labels
- `parameters["values"]`: list[float] — metric values
- `parameters["metric_label"]`: str — e.g., `"Time (s)"`, `"Memory (GB)"`

Multi-series mode:
- `parameters["categories"]`: list[str]
- `parameters["series"]`: dict[str, list[float]] — e.g. `{"FD": [1.2, 3.4], "RTM": [4.5, 8.9]}`
- `parameters["metric_label"]`: str

Optional:
- `parameters["chart_type"]`: `"bar"` (default) or `"line"`
- `parameters["baseline"]`: str — name of baseline method (for annotation)

## Outputs

- `FigureResult.figure`: matplotlib Figure (bar or line chart)
- `FigureResult.saved_paths`: exported paths

## Geophysical Conventions

| Metric         | Axis label              | Notes                          |
|----------------|-------------------------|--------------------------------|
| Time           | `Time (s)` or `Time (h)`| Always show unit               |
| Memory         | `Memory (GB)`           | Peak memory usage              |
| Speedup        | `Speedup (×)`           | Relative to named baseline     |

### Figure Sizing and Typography

| Property       | Value                                    |
|----------------|------------------------------------------|
| Figure size    | Single column: 3.5 × 2.6 in             |
| Font           | Times New Roman (serif), tick=10pt, label=11pt, title=13pt |
| DPI            | 600                                      |
| Export         | PDF (vector) + PNG (preview)             |
| Bar style      | Gradient blue, value annotations, clean grid |
| Spines         | Top and right hidden                     |

## Critical Rules

1. **Always specify the metric unit** in the y-axis label.
2. **Always name the baseline** when showing speedup.
3. **Use clean bar spacing** — avoid too many bars in one figure.
4. Do not use 3D bar charts or pie charts in geophysical papers.

## Common Mistakes to Avoid

- Y axis without unit (e.g., just `"Time"` instead of `"Time (s)"`).
- Speedup without baseline identification.
- Log scale without labeling it as log scale.
- Inconsistent bar widths or colors between related figures.

## Default Behavior

- chart_type: `bar`
- Matplotlib backend (cigvis not used for statistical charts)
- DPI: 600
- Spines: top and right hidden (publication style)

## Example Prompt

```
Plot a grouped bar chart comparing wall-clock time for 3 methods:
FD=1.2s, RTM=4.5s, FWI=18.3s.
Y axis: "Time (s)". Title: "Computational Time Comparison".
Export as PNG (600 dpi).
```
