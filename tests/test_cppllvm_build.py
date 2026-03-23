# ruff: noqa: I001

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from setuptools.errors import SetupError

from cppllvm_build import PackageBuildConfig, asset_name, current_platform


ROOT = Path(__file__).resolve().parents[1]
CTIDY_CONFIG = PackageBuildConfig(
    package_dir=ROOT / "packages/ctidy",
    package_name="ctidy",
    tool_section="ctidy",
    binaries=("clang-tidy", "clang-apply-replacements"),
)
CFORMAT_CONFIG = PackageBuildConfig(
    package_dir=ROOT / "packages/cformat",
    package_name="cformat",
    tool_section="cformat",
    binaries=("clang-format",),
)


class CppLlvmBuildTests(unittest.TestCase):
    @patch("cppllvm_build.machine", return_value="x86_64")
    @patch("cppllvm_build.system", return_value="Linux")
    def test_ctidy_asset_name_uses_llvm_major(self, *_args: object) -> None:
        self.assertEqual(current_platform(CTIDY_CONFIG), ("linux-amd64", ""))
        self.assertEqual(
            asset_name(CTIDY_CONFIG, "clang-tidy"),
            "clang-tidy-20_linux-amd64",
        )

    @patch("cppllvm_build.machine", return_value="amd64")
    @patch("cppllvm_build.system", return_value="Windows")
    def test_cformat_asset_name_uses_package_version(self, *_args: object) -> None:
        self.assertEqual(
            asset_name(CFORMAT_CONFIG, "clang-format"),
            "clang-format-20_windows-amd64.exe",
        )

    @patch("cppllvm_build.machine", return_value="arm64")
    @patch("cppllvm_build.system", return_value="Linux")
    def test_unsupported_platform_raises_clear_error(self, *_args: object) -> None:
        with self.assertRaisesRegex(
            SetupError,
            "Linux/x86_64, macOS/x86_64, macOS/arm64, Windows/x86_64",
        ):
            current_platform(CTIDY_CONFIG)
