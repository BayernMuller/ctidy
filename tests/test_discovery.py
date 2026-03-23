from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from ctidy.discovery import find_compile_commands, validate_compile_commands


class DiscoveryTests(unittest.TestCase):
    def test_find_compile_commands_prefers_known_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            build_dir = root / ".build"
            build_dir.mkdir()
            compile_commands = build_dir / "compile_commands.json"
            compile_commands.write_text("[]", encoding="utf-8")

            self.assertEqual(find_compile_commands(root), compile_commands.resolve())

    def test_validate_compile_commands_accepts_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            compile_commands = root / "compile_commands.json"
            compile_commands.write_text("[]", encoding="utf-8")

            original_cwd = Path.cwd()
            os.chdir(root)
            try:
                validated = validate_compile_commands(compile_commands)
            finally:
                os.chdir(original_cwd)

        self.assertEqual(validated, root.resolve())
