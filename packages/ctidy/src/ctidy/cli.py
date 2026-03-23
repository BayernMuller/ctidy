from __future__ import annotations

import importlib.resources as resources
import os
import runpy
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path

from ctidy import __version__
from ctidy.discovery import find_compile_commands, validate_compile_commands


def has_build_path_argument(argv: list[str]) -> bool:
    for index, arg in enumerate(argv):
        if arg in {"-p", "--build-path"}:
            return index + 1 < len(argv)
        if arg.startswith("-p=") or arg.startswith("--build-path="):
            return True
    return False


def build_path_from_args(argv: list[str]) -> str | None:
    for index, arg in enumerate(argv):
        if arg in {"-p", "--build-path"}:
            if index + 1 >= len(argv):
                return None
            return argv[index + 1]
        if arg.startswith("-p="):
            return arg.split("=", 1)[1]
        if arg.startswith("--build-path="):
            return arg.split("=", 1)[1]
    return None


def rewrite_with_build_path(argv: list[str], build_path: Path) -> list[str]:
    rewritten: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "-p":
            rewritten.extend(["-p", os.fspath(build_path)])
            index += 2
            continue
        if arg == "--build-path":
            rewritten.extend(["-p", os.fspath(build_path)])
            index += 1
            if index < len(argv):
                index += 1
            continue
        if arg.startswith("-p=") or arg.startswith("--build-path="):
            rewritten.extend(["-p", os.fspath(build_path)])
            index += 1
            continue
        rewritten.append(arg)
        index += 1

    return rewritten


def _data_root():
    return resources.files("ctidy").joinpath("data")


def _binary_name(stem: str) -> str:
    return f"{stem}.exe" if os.name == "nt" else stem


def _resource_file(name: str, stack: ExitStack) -> Path:
    resource = _data_root()
    for segment in Path(name).parts:
        resource = resource.joinpath(segment)
    if not resource.is_file():
        raise FileNotFoundError(f"Bundled resource `{name}` is missing.")
    return stack.enter_context(resources.as_file(resource))


def _build_runner_argv(
    argv: list[str], stack: ExitStack, *, include_binaries: bool
) -> tuple[Path, list[str], Path | None]:
    runner = _resource_file("bin/run-clang-tidy.py", stack)
    command = [os.fspath(runner)]
    bin_dir: Path | None = None

    if include_binaries:
        clang_tidy = _resource_file(f"bin/{_binary_name('clang-tidy')}", stack)
        bin_dir = clang_tidy.parent
        command.extend(["-clang-tidy-binary", os.fspath(clang_tidy)])

        apply_replacements = _data_root().joinpath(
            f"bin/{_binary_name('clang-apply-replacements')}"
        )
        if apply_replacements.is_file():
            command.extend(
                [
                    "-clang-apply-replacements-binary",
                    os.fspath(stack.enter_context(resources.as_file(apply_replacements))),
                ]
            )

    command.extend(argv)
    return runner, command, bin_dir


def is_help_requested(argv: list[str]) -> bool:
    return any(arg in {"-h", "--help"} for arg in argv)


def resolve_build_path(argv: list[str], *, auto_discover: bool = True) -> list[str]:
    if has_build_path_argument(argv):
        supplied = build_path_from_args(argv)
        if supplied is None:
            raise ValueError("`-p/--build-path` requires a value.")
        normalized = validate_compile_commands(supplied)
        return rewrite_with_build_path(argv, normalized)

    if not auto_discover:
        return argv

    discovered = find_compile_commands()
    if discovered is None:
        raise FileNotFoundError(
            "compile_commands.json was not found. "
            "Looked for ./build/compile_commands.json, ./.build/compile_commands.json, "
            "./out/build/compile_commands.json, and ./compile_commands.json. "
            "Pass `-p <build-dir>` to point ctidy at your build directory."
        )

    return ["-p", os.fspath(discovered.parent), *argv]


@contextmanager
def patched_argv(argv: list[str]):
    original = sys.argv[:]
    sys.argv = argv
    try:
        yield
    finally:
        sys.argv = original


@contextmanager
def patched_path(bin_dir: Path | None):
    if bin_dir is None:
        yield
        return

    original = os.environ.get("PATH")
    os.environ["PATH"] = os.pathsep.join([os.fspath(bin_dir), original or ""])
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = original


def run_bundled_runner(argv: list[str], *, include_binaries: bool) -> int:
    with ExitStack() as stack:
        runner, runner_argv, bin_dir = _build_runner_argv(
            argv, stack, include_binaries=include_binaries
        )
        with patched_argv(runner_argv), patched_path(bin_dir):
            try:
                runpy.run_path(os.fspath(runner), run_name="__main__")
            except SystemExit as exc:
                code = exc.code
                if code is None:
                    return 0
                if isinstance(code, int):
                    return code
                print(code, file=sys.stderr)
                return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(__version__)
        return 0

    try:
        command_argv = resolve_build_path(
            argv, auto_discover=not is_help_requested(argv)
        )
        returncode = run_bundled_runner(
            command_argv,
            include_binaries=not is_help_requested(command_argv),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ctidy: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ctidy: failed to launch bundled tools: {exc}", file=sys.stderr)
        return 2

    if returncode == 0:
        return 0
    if returncode == 2:
        return 2
    return 1
