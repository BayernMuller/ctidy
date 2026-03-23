from __future__ import annotations

import importlib.resources as resources
import os
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path

from cformat import __version__


def _data_root():
    return resources.files("cformat").joinpath("data")


def _binary_name(stem: str) -> str:
    return f"{stem}.exe" if os.name == "nt" else stem


def _resource_file(name: str, stack: ExitStack) -> Path:
    resource = _data_root()
    for segment in Path(name).parts:
        resource = resource.joinpath(segment)
    if not resource.is_file():
        raise FileNotFoundError(f"Bundled resource `{name}` is missing.")
    return stack.enter_context(resources.as_file(resource))


def run_bundled_binary(argv: list[str]) -> int:
    with ExitStack() as stack:
        binary = _resource_file(f"bin/{_binary_name('clang-format')}", stack)
        completed = subprocess.run([os.fspath(binary), *argv], check=False)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(__version__)
        return 0

    try:
        return run_bundled_binary(argv)
    except FileNotFoundError as exc:
        print(f"cformat: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"cformat: failed to launch bundled tools: {exc}", file=sys.stderr)
        return 2
