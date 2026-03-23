# ruff: noqa: E402,I001

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from cppllvm_build import PackageBuildConfig, make_build_commands


ROOT = Path(__file__).resolve().parent

build_py, bdist_wheel = make_build_commands(
    PackageBuildConfig(
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
