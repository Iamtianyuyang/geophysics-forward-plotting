---
name: geophysics-forward-plotting
description: Entry point and router for the CIGVis-first geophysical forward-modeling plotting framework. Read this first to understand the convention-enforcing workflow and to pick the right sub-skill (velocity model, shot record, wavefield snapshot, multi-method comparison, wiggle, error map, performance, 3D volume, sliceviewer) for a given seismic figure.
---

# Skill: geophysics-forward-plotting (Root)

## Purpose

This is the entry-point skill description for the `geophysics-forward-plotting` framework.
It describes the overall design philosophy and delegates to sub-skills for specific figure types.

This project is **built on CIGVis** as the primary visualization backend.
- CIGVis repository: https://github.com/JintaoLee-Roger/cigvis
- CIGVis Gallery: https://cigvis.readthedocs.io/en/latest/gallery/index.html

## When to Use

Use this root skill description when:
- You need to understand the overall plotting workflow.
- You need to select the correct sub-skill for a given geophysical figure type.
- You need to understand the CIGVis-first architecture.

## Inputs

- A natural-language plotting request or a `FigureTask`/YAML configuration.
- One or more NumPy arrays or `.npy` paths.
- Physical sampling metadata (`dx`, `dz`, `dt`, origins, and units) whenever available.
- Optional method names, error definitions, performance baselines, overlays, and export formats.

## Outputs

- A routed task plan naming the selected executable skill.
- A `FigureResult` containing the figure object, saved paths, summary, and review messages.
- Clear `BackendUnavailableError` guidance for 3D or SliceViewer requests without CIGVis.

## Architecture

```
User request
  -> TaskRouter (identify task_type)
  -> Planner (load FigureTask from YAML or dict)
  -> DataInspectorSkill (load arrays, infer layout)
  -> [Target Skill] (produce figure)
  -> FigureReviewSkill (check conventions)
  -> ExportSkill (save PNG/PDF/SVG)
  -> FigureResult (figure + paths + review messages)
```

CIGVis handles:
- All 2D geophysical image-like plots (via cigvis.mpl)
- 3D volume rendering (via cigvis vispy)
- Interactive SliceViewer

Matplotlib handles:
- Performance bar/line charts
- Fallback when cigvis is unavailable for 2D tasks

## Sub-skills

| Task Type                | Sub-skill SKILL.md                            |
|--------------------------|-----------------------------------------------|
| velocity_model           | velocity-model-plotting/SKILL.md              |
| shot_record              | shot-record-plotting/SKILL.md                 |
| wavefield_snapshot       | wavefield-snapshot-plotting/SKILL.md          |
| multi_method_comparison  | multi-method-comparison/SKILL.md              |
| wiggle                   | wiggle-plotting/SKILL.md                      |
| error_map                | error-map-plotting/SKILL.md                   |
| performance              | performance-plotting/SKILL.md                 |
| volume_3d                | volume-3d-plotting/SKILL.md                   |
| sliceviewer              | sliceviewer-plotting/SKILL.md                 |
| figure_review            | figure-review/SKILL.md                        |

## Geophysical Conventions

These conventions apply to ALL sub-skills unless explicitly overridden:

1. **Depth axis always points downward** (z increases downward).
2. **Time axis always points downward** (t increases downward).
3. **Physical coordinates**, not array indices, must be used for axis labels.
4. **Units must be shown** in axis labels: `Distance (km)`, `Time (s)`, `Depth (km)`.
5. **Multi-panel figures use unified clim** — never independent per-panel normalization.
6. **DPI = 600** for publication (≥ 300 minimum).
7. **Colorbar labels are mandatory** on all figures with color encoding.
8. **Export both PDF (vector) and PNG (preview)** for static figures.

## Typography and Figure Sizing (Paper Standards)

All figures must use a consistent, publication-ready visual style.

### Font

- **Family:** serif (Times New Roman primary; STIXGeneral fallback).
- **Math:** STIX mathtext (`mathtext.fontset = stix`).
- Use LaTeX-style labels when possible: `Velocity (m s$^{-1}$)` instead of `Velocity (m/s)`.

### Font Sizes

| Element              | Size (pt) |
|----------------------|-----------|
| Suptitle (fig title) | 14        |
| Subplot title        | 13        |
| Axis label           | 11        |
| Colorbar label       | 11        |
| Tick labels          | 10        |
| Annotations          | 10        |

### Figure Sizes (Journal Column Widths)

| Layout         | Width (in) | Use when               |
|----------------|------------|------------------------|
| Single column  | 3.5        | Velocity, wavefield, performance |
| 1.5 column     | 5.5        | Shot record, wiggle, error map   |
| Double column  | 7.0        | Multi-method comparison (2×2)    |

Height should preserve a reasonable aspect ratio (typically width × 0.7–0.9).

### Axis Labels

- Shot records and gathers: x = `Offset (km)`, y = `Time (s)`.
- Spatial sections: x = `Distance (km)`, y = `Depth (km)`.
- Colorbar: use physical units with LaTeX: `Velocity (m s$^{-1}$)`, `Pressure (Pa)`.

### Tick and Spine Style

- Tick width: 0.6–0.8 pt, inward direction, labelsize = 10.
- Top and right spines hidden for bar/line charts.
- Grid lines: `alpha=0.25`, dashed, behind data (`zorder=0`).

## Common Mistakes to Avoid

- Plotting with array indices instead of physical coordinates.
- Using independent normalization in multi-method comparison figures.
- Forgetting colorbar labels.
- Setting time or depth axis to point upward.
- Using a non-symmetric colormap for amplitude data.
- Using DPI < 300 for publication figures.

## Default Behavior

- Read this root skill first, then read one specialized plotting skill plus `figure-review`.
- Inspect data before rendering when only paths or ambiguous arrays are supplied.
- Prefer CIGVis for geophysical views and Matplotlib for statistics or 2D fallback.
- Review every rendered result and export only after convention checks complete.
- Ask for missing physical metadata when guessing would change scientific meaning.

## Example Prompt

```
Plot a velocity model from velocity_model.npy with dx=0.025 km, dz=0.025 km.
Use the geophysics-forward-plotting framework with task_type="velocity_model".
Apply all standard geophysical conventions (depth down, colorbar in m/s).
Export as PNG at 600 dpi and PDF.
```
