from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
LOCAL_RUN_CLANG_TIDY = ROOT / "src/ctidy/data/bin/run-clang-tidy.py"
LATEST_RELEASE_URL = "https://api.github.com/repos/llvm/llvm-project/releases/latest"


def project_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


def latest_release_version() -> str:
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    return str(payload["tag_name"]).removeprefix("llvmorg-")


def download_upstream_run_clang_tidy(version: str) -> str:
    url = (
        "https://raw.githubusercontent.com/llvm/llvm-project/"
        f"llvmorg-{version}/clang-tools-extra/clang-tidy/tool/run-clang-tidy.py"
    )
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def write_github_output(path: Path, values: dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    pinned = project_version()
    latest = latest_release_version()
    upstream = download_upstream_run_clang_tidy(pinned)
    local = LOCAL_RUN_CLANG_TIDY.read_text(encoding="utf-8")
    changed = upstream != local

    if changed and args.update:
        LOCAL_RUN_CLANG_TIDY.write_text(upstream, encoding="utf-8")

    print(f"pinned_version={pinned}")
    print(f"latest_version={latest}")
    print(f"run_clang_tidy_changed={'true' if changed else 'false'}")
    print(f"newer_llvm_available={'true' if latest != pinned else 'false'}")

    if args.github_output is not None:
        write_github_output(
            args.github_output,
            {
                "pinned_version": pinned,
                "latest_version": latest,
                "run_clang_tidy_changed": "true" if changed else "false",
                "newer_llvm_available": "true" if latest != pinned else "false",
            },
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
