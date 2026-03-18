from __future__ import annotations

from pathlib import Path

DEFAULT_COMPILE_COMMANDS_CANDIDATES = (
    Path("build/compile_commands.json"),
    Path(".build/compile_commands.json"),
    Path("out/build/compile_commands.json"),
    Path("compile_commands.json"),
)


def find_compile_commands(start_dir: Path | None = None) -> Path | None:
    base_dir = (start_dir or Path.cwd()).resolve()
    for relative_path in DEFAULT_COMPILE_COMMANDS_CANDIDATES:
        candidate = base_dir / relative_path
        if candidate.is_file():
            return candidate
    return None


def normalize_build_path(value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = candidate.resolve()
    if candidate.is_file():
        if candidate.name != "compile_commands.json":
            raise ValueError(f"`{candidate}` is not a compile_commands.json file.")
        return candidate.parent
    return candidate


def validate_compile_commands(build_path: str | Path) -> Path:
    normalized = normalize_build_path(build_path)
    compile_commands = normalized / "compile_commands.json"
    if not compile_commands.is_file():
        raise FileNotFoundError(
            f"compile_commands.json was not found in `{normalized}`."
        )
    return normalized

