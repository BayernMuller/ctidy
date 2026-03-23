# ruff: noqa: I001

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from setuptools.errors import SetupError

from cppllvm_build import (
    LINUX_WHEEL_PLATFORM_TAG,
    PackageBuildConfig,
    asset_name,
    checksum_asset_name,
    current_platform,
    wheel_platform_tag,
)


ROOT = Path(__file__).resolve().parents[1]
ROOT_HELPER_BANNER = (
    "Canonical shared build helper for cppllvm packages.\n"
    "# Package-local copies are vendored so each package can build in isolation."
)
CTIDY_HELPER_BANNER = (
    "Vendored copy of /cppllvm_build.py.\n"
    "# This file stays package-local so `packages/ctidy` can build in isolation."
)
CFORMAT_HELPER_BANNER = (
    "Vendored copy of /cppllvm_build.py.\n"
    "# This file stays package-local so `packages/cformat` can build in isolation."
)
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
    def test_vendored_build_helpers_match_root_copy(self) -> None:
        root_helper = (ROOT / "cppllvm_build.py").read_text(encoding="utf-8")
        self.assertEqual(
            (ROOT / "packages/ctidy/cppllvm_build.py").read_text(encoding="utf-8"),
            root_helper.replace(ROOT_HELPER_BANNER, CTIDY_HELPER_BANNER),
        )
        self.assertEqual(
            (ROOT / "packages/cformat/cppllvm_build.py").read_text(encoding="utf-8"),
            root_helper.replace(ROOT_HELPER_BANNER, CFORMAT_HELPER_BANNER),
        )

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
        self.assertEqual(
            checksum_asset_name(CFORMAT_CONFIG, "clang-format"),
            "clang-format-20_windows-amd64.sha512sum",
        )

    @patch("cppllvm_build.machine", return_value="x86_64")
    @patch("cppllvm_build.system", return_value="Linux")
    def test_linux_wheel_platform_tag_uses_manylinux(self, *_args: object) -> None:
        self.assertEqual(
            wheel_platform_tag("linux_x86_64"),
            LINUX_WHEEL_PLATFORM_TAG,
        )

    @patch("cppllvm_build.machine", return_value="arm64")
    @patch("cppllvm_build.system", return_value="Linux")
    def test_unsupported_platform_raises_clear_error(self, *_args: object) -> None:
        with self.assertRaisesRegex(
            SetupError,
            "Linux/x86_64, macOS/x86_64, macOS/arm64, Windows/x86_64",
        ):
            current_platform(CTIDY_CONFIG)
