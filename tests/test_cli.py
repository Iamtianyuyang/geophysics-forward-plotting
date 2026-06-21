"""CLI 基础测试。"""

import numpy as np
import pytest

from geophysics_forward_plotting.cli.main import app


def test_cli_help():
    # argparse exits with SystemExit(0) on --help
    with pytest.raises(SystemExit) as exc_info:
        app(["--help"])
    assert exc_info.value.code == 0


def test_cli_skills(capsys):
    code = app(["skills"])
    assert code == 0
    out = capsys.readouterr().out
    assert "velocity_model" in out
    assert "shot_record" in out


def test_cli_review_good_config(tmp_path, capsys):
    # 写一个合规配置
    cfg = tmp_path / "good.yaml"
    cfg.write_text(
        "task_type: velocity_model\n"
        "x_label: 'Distance (km)'\n"
        "y_label: 'Depth (km)'\n"
        "colorbar_label: 'Velocity (m/s)'\n"
        "dpi: 600\n"
    )
    code = app(["review", str(cfg)])
    assert code == 0
    out = capsys.readouterr().out
    assert "未发现问题" in out


def test_cli_review_bad_config(tmp_path, capsys):
    # 缺少 colorbar_label 且 dpi 过低
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("task_type: shot_record\ndpi: 72\n")
    code = app(["review", str(cfg)])
    assert code == 0
    out = capsys.readouterr().out
    assert "WARNING" in out


def test_cli_plan(tmp_path, capsys):
    cfg = tmp_path / "plan.yaml"
    cfg.write_text(
        "task_type: velocity_model\n"
        "x_label: 'Distance (km)'\n"
        "y_label: 'Depth (km)'\n"
        "colorbar_label: 'Velocity (m/s)'\n"
    )
    code = app(["plan", str(cfg)])
    assert code == 0


def test_cli_data(tmp_path, capsys):
    code = app(["data", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "velocity_model.npy").exists()
    assert (tmp_path / "shot_record.npy").exists()
    out = capsys.readouterr().out
    assert "示例数据已生成" in out


def test_cli_render(tmp_path, capsys):
    # 生成数据
    np.save(tmp_path / "vel.npy", np.ones((30, 60), dtype=np.float32) * 2000.0)
    cfg = tmp_path / "render.yaml"
    cfg.write_text(
        f"task_type: velocity_model\n"
        f"data_paths:\n  - {tmp_path / 'vel.npy'}\n"
        f"output_dir: {tmp_path}\n"
        f"dx: 0.025\ndz: 0.025\ndpi: 72\n"
    )
    code = app(["render", str(cfg)])
    assert code == 0


def test_cli_agent_skills_validate(capsys):
    code = app(["agent-skills", "validate"])

    assert code == 0
    assert "13 Agent Skills are valid" in capsys.readouterr().out


def test_cli_agent_skills_install(tmp_path, capsys):
    code = app(
        [
            "agent-skills",
            "install",
            "--tool",
            "codex",
            "--destination",
            str(tmp_path),
        ]
    )

    assert code == 0
    assert (tmp_path / ".agents" / "skills" / "shot-record-plotting" / "SKILL.md").is_file()
    assert "Installed 13 skill copies" in capsys.readouterr().out
