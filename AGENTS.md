# Repository Agent Instructions

## Agent Skills

Treat `skills/` as the canonical Agent Skills catalog. Do not duplicate scientific
plotting rules in tool-specific instruction files.

For any geophysical plotting, figure review, or method-evaluation request:

1. Read `skills/geophysics-forward-plotting/SKILL.md`.
2. Select and read the one specialized `skills/<name>/SKILL.md` matching the request.
3. Read `skills/data-inspector/SKILL.md` when layout, units, or physical axes are uncertain.
4. Apply `skills/figure-review/SKILL.md` before reporting completion.
5. Use the executable package under `src/geophysics_forward_plotting/`; do not reimplement CIGVis.

Non-negotiable scientific rules:

- Use physical coordinates and units instead of sample indices.
- Point time and depth axes downward for image-like sections.
- Use symmetric limits for signed seismic amplitude and signed error.
- Use one global color limit and one shared colorbar for method comparisons.
- State relative-error formulas and performance baselines explicitly.
- Raise a clear error when CIGVis-only 3D features are unavailable.

Validate the catalog with:

```bash
gfp agent-skills validate
```

Install project-local copies for supported coding tools with:

```bash
gfp agent-skills install --tool codex claude cursor gemini copilot opencode
```

