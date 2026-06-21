"""GFP 命令行接口。

命令
----
  gfp render <config.yaml>   — 根据配置文件渲染图件
  gfp plan   <config.yaml>   — 解析配置并显示计划（不渲染）
  gfp review <config.yaml>   — 审查配置是否符合地球物理规范
  gfp skills                 — 列出所有已注册技能
  gfp data   <dir>           — 生成示例 mock 数据到指定目录
  gfp --version              — 显示版本
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from geophysics_forward_plotting import __version__


def _cmd_render(args: argparse.Namespace) -> int:
    from geophysics_forward_plotting.agent.planner import Planner
    from geophysics_forward_plotting.agent.plotting_agent import PlottingAgent
    from geophysics_forward_plotting.core.io import load_array
    from geophysics_forward_plotting.core.models import DataContext

    config = Path(args.config)
    print(f"[gfp] 加载配置：{config}")
    task = Planner.from_yaml(config)

    arrays = []
    for p in task.data_paths:
        if p.exists():
            arrays.append(load_array(p))
        else:
            print(f"[gfp] 警告：数据文件不存在，跳过 {p}", file=sys.stderr)

    ctx = DataContext(raw_data=tuple(arrays))
    agent = PlottingAgent()
    result = agent.run(task, ctx)

    print(f"[gfp] 完成：{result.summary}")
    for path in result.saved_paths:
        print(f"  -> {path}")
    if result.review_messages:
        print("[gfp] 规范检查：")
        for msg in result.review_messages:
            print(f"  {msg}")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    from geophysics_forward_plotting.agent.planner import Planner
    from geophysics_forward_plotting.agent.plotting_agent import _build_default_registry

    config = Path(args.config)
    task = Planner.from_yaml(config)
    registry = _build_default_registry()
    skill = registry.resolve(task)

    print(f"任务类型  : {task.task_type}")
    print(f"标题      : {task.title or '（未设置）'}")
    print(f"数据路径  : {[str(p) for p in task.data_paths]}")
    print(f"输出目录  : {task.output_dir}")
    print(f"导出格式  : {task.export_formats}")
    print(f"解析 Skill: {skill.name if skill else '（无匹配技能）'}")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    from geophysics_forward_plotting.agent.planner import Planner
    from geophysics_forward_plotting.skills.figure_review_skill import FigureReviewSkill

    config = Path(args.config)
    task = Planner.from_yaml(config)
    reviewer = FigureReviewSkill()
    msgs = reviewer._check_task(task)
    if msgs:
        print(f"[gfp review] {len(msgs)} 条规范提示：")
        for m in msgs:
            print(f"  {m}")
    else:
        print("[gfp review] 配置符合地球物理绘图规范，未发现问题。")
    return 0


def _cmd_skills(_args: argparse.Namespace) -> int:
    from geophysics_forward_plotting.agent.plotting_agent import _build_default_registry

    registry = _build_default_registry()
    print(f"[gfp] 已注册 {len(registry)} 个技能：")
    for skill in registry:
        print(f"  {skill.name:<30} priority={skill.priority}  {skill.description}")
    return 0


def _cmd_data(args: argparse.Namespace) -> int:
    from geophysics_forward_plotting.utils.sample_data import ensure_example_data

    data_dir = Path(args.dir)
    ensure_example_data(data_dir)
    print(f"[gfp] 示例数据已生成至：{data_dir}")
    return 0


def _cmd_agent_skills(args: argparse.Namespace) -> int:
    from geophysics_forward_plotting.agent_skills import (
        TOOL_TARGETS,
        discover_agent_skills,
        install_agent_skills,
        resolve_agent_skills_root,
        validate_agent_skills,
    )

    skills_root = resolve_agent_skills_root(args.project_root)

    if args.agent_skills_command == "list":
        for skill in discover_agent_skills(skills_root):
            print(f"{skill.name:<32} {skill.description}")
        return 0

    if args.agent_skills_command == "validate":
        report = validate_agent_skills(skills_root)
        if report.is_valid:
            print(f"[gfp] {len(report.skills)} Agent Skills are valid")
            return 0
        for issue in report.issues:
            print(f"[ERROR] {issue.skill}: {issue.message}", file=sys.stderr)
        return 1

    installed = install_agent_skills(
        skills_root,
        args.destination,
        args.tool,
        force=args.force,
    )
    selected = sorted({str(path.parent) for path in installed})
    print(f"[gfp] Installed {len(installed)} skill copies")
    for target in selected:
        print(f"  -> {target}")
    print(f"[gfp] Tool targets: {', '.join(sorted(TOOL_TARGETS))}")
    return 0


def app(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gfp",
        description="CIGVis-first 地球物理正演绘图框架",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # render
    p_render = sub.add_parser("render", help="根据 YAML 配置渲染图件")
    p_render.add_argument("config", help="配置文件路径（.yaml）")

    # plan
    p_plan = sub.add_parser("plan", help="解析配置，展示任务计划（不渲染）")
    p_plan.add_argument("config", help="配置文件路径（.yaml）")

    # review
    p_review = sub.add_parser("review", help="检查配置是否符合地球物理规范")
    p_review.add_argument("config", help="配置文件路径（.yaml）")

    # skills
    sub.add_parser("skills", help="列出所有已注册技能")

    # data
    p_data = sub.add_parser("data", help="生成示例 mock 数据")
    p_data.add_argument(
        "dir",
        nargs="?",
        default="examples/data",
        help="输出目录（默认 examples/data）",
    )

    p_agent_skills = sub.add_parser(
        "agent-skills",
        help="list, validate, or install canonical Agent Skills",
    )
    agent_sub = p_agent_skills.add_subparsers(
        dest="agent_skills_command",
        metavar="ACTION",
        required=True,
    )
    for action in ("list", "validate"):
        action_parser = agent_sub.add_parser(action)
        action_parser.add_argument("--project-root", default=".")

    install_parser = agent_sub.add_parser("install")
    install_parser.add_argument("--project-root", default=".")
    install_parser.add_argument("--destination", default=".")
    install_parser.add_argument(
        "--tool",
        nargs="+",
        choices=("all", "codex", "claude", "cursor", "gemini", "copilot", "opencode"),
        default=["all"],
    )
    install_parser.add_argument("--force", action="store_true")

    ns = parser.parse_args(argv)

    handlers = {
        "render": _cmd_render,
        "plan": _cmd_plan,
        "review": _cmd_review,
        "skills": _cmd_skills,
        "data": _cmd_data,
        "agent-skills": _cmd_agent_skills,
    }

    if ns.command not in handlers:
        parser.print_help()
        return 0

    try:
        return handlers[ns.command](ns)
    except Exception as exc:
        print(f"[gfp] 错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(app())
