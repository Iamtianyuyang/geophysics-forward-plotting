---
name: data-inspector
description: Load .npy arrays referenced by a figure task and infer their layout (nz×nx, nt×nx, nz×ny×nx), data kind (velocity, amplitude, error, volume), and value range, attaching the result to a DataContext. Runs automatically before every plot when only file paths are given; rarely invoked on its own.
---

# Skill: data-inspector

## Purpose

Turn raw `.npy` file paths into a populated `DataContext` so plotting skills receive
loaded arrays plus inferred physical metadata. This is the first step of every
`PlottingAgent.run()` call when the caller passes `data_paths` but no in-memory arrays.

## When to Use

- A task carries `data_paths` (file paths) but no `raw_data` arrays yet.
- You want to inspect an unfamiliar array's shape, layout, and value range before plotting.
- Called automatically by `PlottingAgent`; you seldom invoke it directly.

## Inputs

| Parameter    | Type            | Description                                  |
|--------------|-----------------|----------------------------------------------|
| `task_type`  | any             | Used only to hint the expected layout        |
| `data_paths` | list[str]       | One or more `.npy` files to load             |

## What It Infers

| Field             | How it is inferred                                            |
|-------------------|--------------------------------------------------------------|
| `shape` / `ndim`  | Directly from the loaded array                               |
| `inferred_layout` | 2D → `nz_nx` / `nt_nx`; 3D → `nz_ny_nx`                       |
| `data_kind`       | Velocity vs amplitude vs error vs volume, from value range   |
| `value_range`     | `(min, max)` of the primary array                            |

## Outputs

- `FigureResult.metadata["context"]`: a populated `DataContext` (arrays + metadata).
- `FigureResult.summary`: a one-line description of what was loaded.

## Notes

- Low routing priority (99): it never wins over a plotting skill in `TaskRouter`;
  the agent calls it explicitly as a preprocessing step.
- If no `data_paths` and no `raw_data` are present, it returns an empty context
  rather than raising - the downstream plotting skill reports the missing data.

## Geophysical Conventions

- Treat layout inference as a hypothesis unless `dx`, `dz`, `dt`, or an explicit layout confirms it.
- Preserve original values and dtype; inspection must not normalize or transpose data.
- Report physical sampling separately from array shape. Never label sample indices as km or s.
- Interpret 2D amplitude data as `(nt, nx)` for shot records and `(nz, nx)` for spatial fields.

## Common Mistakes to Avoid

- Guessing time versus depth from shape alone when task metadata is available.
- Loading pickle-enabled NumPy objects from untrusted files.
- Replacing non-finite values silently instead of reporting them.
- Treating every positive-valued array as velocity without checking task type and units.

## Default Behavior

- Load `.npy` files with pickle disabled.
- Inspect the first array as primary and preserve every array in `DataContext.raw_data`.
- Compute shape, dimension count, finite value range, data kind, and inferred layout.
- Return an empty context only when no path or in-memory array is supplied.

## Example Prompt

```text
Inspect examples/data/shot_record.npy before plotting. Confirm its shape, inferred
layout, finite amplitude range, and whether dt/dx metadata is sufficient to build
physical Time (s) and Receiver position (km) axes. Do not alter the array.
```
