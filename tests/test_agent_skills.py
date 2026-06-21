from pathlib import Path

from geophysics_forward_plotting.agent_skills import (
    TOOL_TARGETS,
    discover_agent_skills,
    install_agent_skills,
    validate_agent_skills,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / "skills"


def test_canonical_agent_skills_are_valid() -> None:
    report = validate_agent_skills(SKILLS_ROOT)

    assert report.is_valid, [f"{issue.skill}: {issue.message}" for issue in report.issues]
    assert len(report.skills) == 13


def test_discovery_includes_root_and_specialized_skills() -> None:
    names = {skill.name for skill in discover_agent_skills(SKILLS_ROOT)}

    assert "geophysics-forward-plotting" in names
    assert "shot-record-plotting" in names
    assert "method-evaluation" in names


def test_install_agent_skills_for_all_supported_tools(tmp_path: Path) -> None:
    installed = install_agent_skills(SKILLS_ROOT, tmp_path, ["all"])

    assert len(installed) == 13 * len(TOOL_TARGETS)
    for relative_target in TOOL_TARGETS.values():
        target = tmp_path / relative_target
        assert (target / "geophysics-forward-plotting" / "SKILL.md").is_file()
        assert (target / ".gfp-agent-skills.json").is_file()
