# ruff: noqa: E402,I001

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from cppllvm_build import PackageBuildConfig, make_build_commands


ROOT = Path(__file__).resolve().parent

build_py, bdist_wheel = make_build_commands(
    PackageBuildConfig(
        package_dir=ROOT,
        package_name="cformat",
        tool_section="cformat",
        binaries=("clang-format",),
        download_env_vars=("CFORMAT_DOWNLOAD_DIR",),
    )
)
