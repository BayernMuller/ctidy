from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from ctidy.cli import resolve_build_path, rewrite_with_build_path


class CliTests(unittest.TestCase):
    def test_rewrite_with_build_path_normalizes_long_option(self) -> None:
        build_path = Path("/tmp/build")
        self.assertEqual(
            rewrite_with_build_path(
                ["--build-path", "out", "--checks=*", "main.cc"],
                build_path,
            ),
            ["-p", os.fspath(build_path), "--checks=*", "main.cc"],
        )

    def test_resolve_build_path_auto_discovers_build_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            build_dir = root / "build"
            build_dir.mkdir()
            (build_dir / "compile_commands.json").write_text("[]", encoding="utf-8")

            original_cwd = Path.cwd()
            os.chdir(root)
            try:
                resolved = resolve_build_path(["main.cc"])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(
            resolved,
            ["-p", os.fspath(build_dir.resolve()), "main.cc"],
        )
