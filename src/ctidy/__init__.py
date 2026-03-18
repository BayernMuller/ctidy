import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("ctidy")
except PackageNotFoundError:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    match = re.search(
        r'^version\s*=\s*"(?P<version>[^"]+)"',
        pyproject.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    __version__ = match.group("version") if match else "0.0.0"
