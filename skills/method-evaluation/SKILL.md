---
name: method-evaluation
description: Evaluate a new geophysical method against one or more baseline methods — automatically produces a side-by-side comparison, error maps vs a reference, residual maps vs each baseline, a runtime chart, quantitative metrics (RMSE, max error, correlation), and a strengths/weaknesses verdict. Use when the user has a new modeling/inversion method and wants to validate where it wins and loses against existing methods.
---

# Skill: method-evaluation

## Purpose

A higher-level **agent**, not a single plotting skill. Given a new method's result
and a set of baseline results (optionally a reference / ground-truth solution), it
orchestrates the plotting skills to build a complete comparison study and a written
verdict on the new method's advantages and disadvantages.

It is implemented as `MethodEvaluationAgent` and composes existing skills through
`PlottingAgent`, so every figure inherits the geophysical conventions and the
automatic figure review.

## When to Use

- You developed a new forward-modeling or inversion method and need to validate it.
- You want an apples-to-apples comparison against baseline methods, with numbers.
- You want the strengths and weaknesses summarized, not just figures.

## Inputs

| Input | Type | Description |
|-------|------|-------------|
| `new_method` | `MethodResult(name, data, runtime?)` | The method under evaluation |
| `baselines` | list of `MethodResult` | One or more baseline methods (same shape) |
| `reference` | array, optional | Ground truth / analytic solution for accuracy metrics |
| `figure_kind` | str | `shot_record`, `wavefield_snapshot`, or `velocity_model` (sets axis labels) |
| `dx` / `dz` / `dt` | float | Physical sampling intervals |

## What It Produces

1. **Comparison figure** — all methods side by side, unified color scale (`multi-method-comparison`).
2. **Error map** — new method minus reference, signed (`error-map-plotting`), if a reference is given.
3. **Residual maps** — new method minus each baseline, one per baseline.
4. **Performance chart** — runtime bar chart (`performance-plotting`), if every method has a `runtime`.
5. **Metrics** — RMSE, max absolute error, correlation vs reference, runtime per method.
6. **Verdict** — `strengths` and `weaknesses` lists derived from the metric rankings.

## Outputs

- `EvaluationReport.saved_paths` — every figure produced.
- `EvaluationReport.metrics` — per-method `MethodMetrics`.
- `EvaluationReport.strengths` / `.weaknesses` — the written conclusion.
- `EvaluationReport.render_text()` — a printable report.

## Notes

- Accuracy metrics (RMSE, correlation) require a `reference`; without one the agent
  still produces the comparison, residual maps, and performance chart, and says so.
- The comparison figure shows at most 4 methods (panel limit); extras are noted.
- Residual figures for each baseline are written to their own subfolder so filenames
  do not collide.

## Geophysical Conventions

- Compare arrays only when shape, physical extent, sampling, units, and quantity match.
- Use one global color limit for the primary side-by-side comparison.
- Define residual sign as `candidate - reference` or `candidate - baseline` consistently.
- Report RMSE and maximum error in physical units; identify dimensionless metrics.
- Name the runtime baseline and record comparable hardware/runtime conditions when available.

## Common Mistakes to Avoid

- Ranking methods whose grids, source wavelets, preprocessing, or units differ.
- Using independently normalized panels that hide amplitude bias.
- Claiming accuracy improvements without a reference solution.
- Treating correlation as a substitute for amplitude error.
- Declaring speedup when timing scope or hardware differs.

## Default Behavior

- Validate shape compatibility before computing metrics.
- Produce a unified comparison, then reference errors, baseline residuals, and performance.
- Limit the main comparison to four readable panels and report omitted methods.
- Keep verdicts traceable to metrics and explicitly note unavailable evidence.

## Example Prompt

```
I have a new method "Hybrid FWI" plus two baselines "RTM" and "FD-coarse",
all producing shot records of the same shape, and an analytic reference.
Evaluate the new method: compare them, show where it differs, compare runtime,
and tell me its strengths and weaknesses.
```
