# ruff: noqa: E402,I001

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_SPEC = importlib.util.spec_from_file_location(
    "_cformat_cppllvm_build",
    ROOT / "cppllvm_build.py",
)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("Failed to load cformat package build helpers.")
BUILD_HELPERS = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = BUILD_HELPERS
MODULE_SPEC.loader.exec_module(BUILD_HELPERS)

build_py, bdist_wheel = BUILD_HELPERS.make_build_commands(
    BUILD_HELPERS.PackageBuildConfig(
        package_dir=ROOT,
        package_name="cformat",
        tool_section="cformat",
        binaries=("clang-format",),
        download_env_vars=("CFORMAT_DOWNLOAD_DIR",),
    )
)
