"""Discovery, validation, and project-local installation for Agent Skills."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_SECTIONS = (
    "Purpose",
    "When to Use",
    "Inputs",
    "Outputs",
    "Geophysical Conventions",
    "Common Mistakes to Avoid",
    "Default Behavior",
    "Example Prompt",
)

# Project-local discovery paths used by Agent Skills-aware coding tools.
TOOL_TARGETS: dict[str, Path] = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "cursor": Path(".cursor/skills"),
    "gemini": Path(".gemini/skills"),
    "copilot": Path(".github/skills"),
    "opencode": Path(".opencode/skills"),
}


@dataclass(frozen=True, slots=True)
class AgentSkillSpec:
    """Metadata extracted from one canonical SKILL.md."""

    name: str
    description: str
    path: Path


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    skill: str
    message: str


@dataclass(slots=True)
class CatalogValidation:
    skills: tuple[AgentSkillSpec, ...] = ()
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues


def find_project_root(start: str | Path | None = None) -> Path:
    """Find a checkout containing the canonical root skill."""

    current = Path(start or Path.cwd()).resolve()
    candidates = (current, *current.parents)
    for candidate in candidates:
        root_skill = candidate / "skills" / "geophysics-forward-plotting" / "SKILL.md"
        if root_skill.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find skills/geophysics-forward-plotting/SKILL.md from " f"{current}"
    )


def resolve_agent_skills_root(start: str | Path | None = None) -> Path:
    """Prefer checkout skills and fall back to skills bundled in an installed wheel."""

    try:
        return find_project_root(start) / "skills"
    except FileNotFoundError:
        bundled = Path(__file__).resolve().parent / "_agent_skills"
        root_skill = bundled / "geophysics-forward-plotting" / "SKILL.md"
        if root_skill.is_file():
            return bundled
        raise


def _read_frontmatter(skill_file: Path) -> tuple[dict[str, Any], str]:
    content = skill_file.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    try:
        frontmatter_text, body = content[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("frontmatter must end with a standalone --- line") from exc
    metadata = yaml.safe_load(frontmatter_text)
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return metadata, body


def discover_agent_skills(skills_root: str | Path) -> tuple[AgentSkillSpec, ...]:
    """Discover canonical skills without importing executable plotting skills."""

    root = Path(skills_root).resolve()
    specs: list[AgentSkillSpec] = []
    for skill_file in sorted(root.glob("*/SKILL.md")):
        metadata, _ = _read_frontmatter(skill_file)
        name = metadata.get("name")
        description = metadata.get("description")
        if isinstance(name, str) and isinstance(description, str):
            specs.append(AgentSkillSpec(name.strip(), description.strip(), skill_file.parent))
    return tuple(specs)


def validate_agent_skills(skills_root: str | Path) -> CatalogValidation:
    """Validate names, metadata, required domain sections, and duplicate entries."""

    root = Path(skills_root).resolve()
    issues: list[ValidationIssue] = []
    specs: list[AgentSkillSpec] = []
    seen: set[str] = set()

    if not root.is_dir():
        return CatalogValidation(issues=[ValidationIssue("catalog", f"missing directory: {root}")])

    for skill_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            issues.append(ValidationIssue(skill_dir.name, "SKILL.md is missing"))
            continue

        try:
            metadata, body = _read_frontmatter(skill_file)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            issues.append(ValidationIssue(skill_dir.name, str(exc)))
            continue

        unexpected = set(metadata) - {"name", "description"}
        if unexpected:
            issues.append(
                ValidationIssue(
                    skill_dir.name,
                    f"unexpected frontmatter keys: {sorted(unexpected)}",
                )
            )

        name = metadata.get("name")
        description = metadata.get("description")
        if not isinstance(name, str) or not name.strip():
            issues.append(ValidationIssue(skill_dir.name, "frontmatter name is missing"))
            continue
        name = name.strip()
        if not SKILL_NAME_PATTERN.fullmatch(name) or len(name) > 64:
            issues.append(
                ValidationIssue(name, "name must be hyphen-case and at most 64 characters")
            )
        if name != skill_dir.name:
            issues.append(ValidationIssue(name, f"directory must be named {name}"))
        if name in seen:
            issues.append(ValidationIssue(name, "duplicate skill name"))
        seen.add(name)

        if not isinstance(description, str) or not description.strip():
            issues.append(ValidationIssue(name, "frontmatter description is missing"))
            description = ""
        elif len(description) > 1024:
            issues.append(ValidationIssue(name, "description exceeds 1024 characters"))

        headings = set(re.findall(r"^## (.+?)\s*$", body, flags=re.MULTILINE))
        for section in REQUIRED_SECTIONS:
            if section not in headings:
                issues.append(ValidationIssue(name, f"missing section: {section}"))

        openai_file = skill_dir / "agents" / "openai.yaml"
        if not openai_file.is_file():
            issues.append(ValidationIssue(name, "agents/openai.yaml is missing"))
        else:
            try:
                openai_metadata = yaml.safe_load(openai_file.read_text(encoding="utf-8"))
                interface = openai_metadata.get("interface", {})
                default_prompt = interface.get("default_prompt", "")
                if not interface.get("display_name") or not interface.get("short_description"):
                    issues.append(ValidationIssue(name, "OpenAI interface metadata is incomplete"))
                if f"${name}" not in default_prompt:
                    issues.append(
                        ValidationIssue(name, f"OpenAI default_prompt must mention ${name}")
                    )
            except (AttributeError, OSError, UnicodeError, yaml.YAMLError) as exc:
                issues.append(ValidationIssue(name, f"invalid agents/openai.yaml: {exc}"))

        specs.append(AgentSkillSpec(name, str(description).strip(), skill_dir))

    if not specs:
        issues.append(ValidationIssue("catalog", "no skills discovered"))
    return CatalogValidation(tuple(specs), issues)


def expand_tool_names(tools: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    requested = list(tools)
    if "all" in requested:
        return tuple(TOOL_TARGETS)
    unknown = set(requested) - set(TOOL_TARGETS)
    if unknown:
        raise ValueError(f"Unsupported tools: {sorted(unknown)}")
    return tuple(dict.fromkeys(requested))


def install_agent_skills(
    skills_root: str | Path,
    project_root: str | Path,
    tools: list[str] | tuple[str, ...],
    *,
    force: bool = False,
) -> tuple[Path, ...]:
    """Copy canonical skills into project-local tool discovery directories."""

    validation = validate_agent_skills(skills_root)
    if not validation.is_valid:
        messages = "; ".join(f"{issue.skill}: {issue.message}" for issue in validation.issues)
        raise ValueError(f"Cannot install invalid Agent Skills catalog: {messages}")

    project = Path(project_root).resolve()
    project.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    selected_tools = expand_tool_names(tools)

    conflicts = [
        project / TOOL_TARGETS[tool] / spec.name
        for tool in selected_tools
        for spec in validation.skills
        if (project / TOOL_TARGETS[tool] / spec.name).exists()
    ]
    if conflicts and not force:
        preview = ", ".join(str(path) for path in conflicts[:3])
        suffix = " ..." if len(conflicts) > 3 else ""
        raise FileExistsError(
            f"{len(conflicts)} skill directories already exist: {preview}{suffix}; "
            "pass --force to refresh managed files"
        )

    for tool in selected_tools:
        target_root = project / TOOL_TARGETS[tool]
        target_root.mkdir(parents=True, exist_ok=True)
        for spec in validation.skills:
            destination = target_root / spec.name
            shutil.copytree(spec.path, destination, dirs_exist_ok=force)
            installed.append(destination)

        marker = {
            "format_version": 1,
            "source": str(Path(skills_root).resolve()),
            "tool": tool,
            "skills": [spec.name for spec in validation.skills],
        }
        (target_root / ".gfp-agent-skills.json").write_text(
            json.dumps(marker, indent=2) + "\n", encoding="utf-8"
        )

    return tuple(installed)
