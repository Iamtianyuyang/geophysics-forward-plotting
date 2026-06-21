# Agent Skills Integration

## Design

`skills/` is the single source of truth. Each folder follows the Agent Skills layout:

```text
skills/<skill-name>/
  SKILL.md
  agents/openai.yaml  # optional product metadata
```

The portable catalog and progressive-disclosure approach are informed by
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). This repository
adds geophysical domain contracts, executable Python skills, and deterministic validation.

Tool-specific files (`AGENTS.md`, `CLAUDE.md`, Cursor rules, and Copilot instructions)
only route the coding agent to the canonical catalog. They intentionally do not repeat
scientific conventions.

## Validate

Create and activate the Conda environment, then validate all frontmatter and required sections:

```bash
conda env create -f environment.yml
conda activate geophysics-forward-plotting
gfp agent-skills validate
```

From a fresh checkout before package installation:

```bash
conda run -n geophysics-forward-plotting python scripts/manage_agent_skills.py validate
```

## Tool Targets

| Tool | Project-local skill target | Repository instruction entry |
|---|---|---|
| OpenAI Codex | `.agents/skills/` | `AGENTS.md` |
| Claude Code | `.claude/skills/` | `CLAUDE.md` |
| Cursor | `.cursor/skills/` | `.cursor/rules/` |
| Gemini CLI | `.gemini/skills/` | `GEMINI.md` |
| GitHub Copilot | `.github/skills/` | `.github/copilot-instructions.md` |
| OpenCode | `.opencode/skills/` | `AGENTS.md` |

Install canonical copies for one or more tools:

```bash
gfp agent-skills install --tool codex claude cursor
gfp agent-skills install --tool all
```

Use `--destination PATH` to prepare another project. Existing skill directories are
never overwritten unless `--force` is supplied. Generated copies and their manifest
are ignored by Git in this repository.

## Agent Workflow

1. Read `geophysics-forward-plotting` to route the request.
2. Read `cigvis-api-plotting` for API selection and axis-order conversion.
3. Read one specialized plotting or method-evaluation skill.
4. Read `data-inspector` when layout or physical metadata is uncertain.
5. Execute through the Python package or `gfp` CLI.
6. Apply `figure-review` before export and completion.

The text skills guide coding agents; executable classes under
`src/geophysics_forward_plotting/skills/` perform deterministic plotting and review.
