from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from cformat import __version__
from cformat.cli import main


class CFormatCliTests(unittest.TestCase):
    def test_main_version_prints_package_version(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            returncode = main(["--version"])

        self.assertEqual(returncode, 0)
        self.assertEqual(stdout.getvalue().strip(), __version__)
