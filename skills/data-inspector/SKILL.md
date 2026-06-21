---
name: data-inspector
description: Load NPY, raw BIN, SEG-Y, and Seismic Unix (SU) files referenced by a figure task; preserve source metadata and infer nz-by-nx, nt-by-nx, or nz-by-ny-by-nx layouts. Use whenever seismic input format, binary shape, endianness, trace order, sample interval, or physical layout needs inspection before plotting.
---

# Skill: data-inspector

## Purpose

Turn `.npy`, `.bin`, `.sgy`/`.segy`, and `.su` paths into a populated
`DataContext` so plotting skills receive arrays plus source and sampling metadata. This is the first step of every
`PlottingAgent.run()` call when the caller passes `data_paths` but no in-memory arrays.

## When to Use

- A task carries `data_paths` (file paths) but no `raw_data` arrays yet.
- You want to inspect an unfamiliar array's shape, layout, and value range before plotting.
- Called automatically by `PlottingAgent`; you seldom invoke it directly.

## Inputs

| Parameter    | Type            | Description                                  |
|--------------|-----------------|----------------------------------------------|
| `task_type`  | any             | Used only to hint the expected layout        |
| `data_paths` | list[str]       | NPY, BIN, SEG-Y, or SU files                 |
| `data_options` | mapping or list[mapping] | Shared options or one mapping per path |

### Format Options

| Format | Required/important options | Normalized result |
|---|---|---|
| NPY | none | Original array and dtype |
| BIN | `shape`; optional `dtype`, `endianness`, `order`, `offset`, `data_layout` | Explicitly reshaped raw values |
| SEG-Y/SU | optional `endian`, `strict`, `ignore_geometry`, `mmap`, `output_layout`, `shape` | Default `(samples, traces)` / `nt_nx` |

Never infer raw BIN shape or dtype from file size alone. Ask the user for them.
For SEG-Y/SU, use `output_layout: traces_samples` only when downstream code
explicitly expects `(nx, nt)`. Use `shape: [nz, ny, nx]` only when trace order
and the intended 3D geometry are known.

## What It Infers

| Field             | How it is inferred                                            |
|-------------------|--------------------------------------------------------------|
| `shape` / `ndim`  | Directly from the loaded array                               |
| `inferred_layout` | 2D → `nz_nx` / `nt_nx`; 3D → `nz_ny_nx`                       |
| `data_kind`       | Velocity vs amplitude vs error vs volume, from value range   |
| `value_range`     | `(min, max)` of the primary array                            |

`parameters.data_layout` is authoritative when present. Inspect in-memory
`DataContext.raw_data` as rigorously as arrays loaded from paths.

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
- Convert the SEG-Y/SU microsecond sample interval to seconds and retain both values.

## Common Mistakes to Avoid

- Guessing time versus depth from shape alone when task metadata is available.
- Loading pickle-enabled NumPy objects from untrusted files.
- Replacing non-finite values silently instead of reporting them.
- Treating every positive-valued array as velocity without checking task type and units.
- Skipping inspection because the caller supplied an in-memory NumPy array.
- Guessing a BIN shape, dtype, byte order, or C/Fortran memory order.
- Treating SEG-Y trace-major `(traces, samples)` storage as `(time, receiver)` without conversion.
- Reconstructing a 3D SEG-Y volume without a verified inline/crossline trace order.

## Default Behavior

- Load `.npy` files with pickle disabled and raw BIN with explicit metadata.
- Read SEG-Y/SU through `segyio`; default to `(samples, traces)` and preserve header `dt`.
- Inspect the first array as primary and preserve every array in `DataContext.raw_data`.
- Compute shape, dimension count, finite value range, data kind, and inferred layout.
- Honor an explicit `data_layout` before applying a shape heuristic.
- Return an empty context only when no path or in-memory array is supplied.

## Example Prompt

```text
Inspect field_shot.segy before plotting. Confirm trace and sample counts, header
sample interval, endian, normalized `(nt, nx)` layout, finite amplitude range,
and whether receiver coordinates are available. Do not normalize amplitudes.
```
