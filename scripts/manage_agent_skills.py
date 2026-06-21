"""Run the repository Agent Skills manager without installing the package first."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "src"))
    app = import_module("geophysics_forward_plotting.cli.main").app
    raise SystemExit(app(["agent-skills", *sys.argv[1:]]))
