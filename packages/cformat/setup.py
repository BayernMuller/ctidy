# ruff: noqa: I001

import importlib.util
from pathlib import Path

from setuptools import setup

ROOT = Path(__file__).resolve().parent
MODULE_SPEC = importlib.util.spec_from_file_location(
    "_cformat_build_hooks",
    ROOT / "build_hooks.py",
)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("Failed to load cformat build hooks.")
BUILD_HOOKS = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(BUILD_HOOKS)

setup(
    cmdclass={
        "build_py": BUILD_HOOKS.build_py,
        "bdist_wheel": BUILD_HOOKS.bdist_wheel,
    }
)
