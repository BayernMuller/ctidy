# ruff: noqa: I001

import sys
from pathlib import Path

from setuptools import setup

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_hooks import bdist_wheel, build_py


setup(
    cmdclass={
        "build_py": build_py,
        "bdist_wheel": bdist_wheel,
    }
)
