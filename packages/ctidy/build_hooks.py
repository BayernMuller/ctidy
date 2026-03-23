# ruff: noqa: E402,I001

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_SPEC = importlib.util.spec_from_file_location(
    "_ctidy_cppllvm_build",
    ROOT / "cppllvm_build.py",
)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("Failed to load ctidy package build helpers.")
BUILD_HELPERS = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = BUILD_HELPERS
MODULE_SPEC.loader.exec_module(BUILD_HELPERS)

build_py, bdist_wheel = BUILD_HELPERS.make_build_commands(
    BUILD_HELPERS.PackageBuildConfig(
        package_dir=ROOT,
        package_name="ctidy",
        tool_section="ctidy",
        binaries=("clang-tidy", "clang-apply-replacements"),
        copied_files=(
            (ROOT / "src/ctidy/data/bin/run-clang-tidy.py", "bin/run-clang-tidy.py"),
        ),
        include_resource_headers=True,
        download_env_vars=("CTIDY_DOWNLOAD_DIR", "CTIDY_LLVM_DOWNLOAD_DIR"),
    )
)
