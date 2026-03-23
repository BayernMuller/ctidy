from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PYPROJECTS = {
    "ctidy": ROOT / "packages" / "ctidy" / "pyproject.toml",
    "cformat": ROOT / "packages" / "cformat" / "pyproject.toml",
}
LOCAL_RUN_CLANG_TIDY = (
    ROOT / "packages" / "ctidy" / "src" / "ctidy" / "data" / "bin" / "run-clang-tidy.py"
)
LATEST_RELEASE_URL = "https://api.github.com/repos/llvm/llvm-project/releases/latest"
LATEST_PREBUILT_RELEASE_URL = (
    "https://api.github.com/repos/muttleyxd/clang-tools-static-binaries/releases/latest"
)


def pyproject_data(package: str) -> dict:
    return tomllib.loads(PACKAGE_PYPROJECTS[package].read_text(encoding="utf-8"))


def project_version(package: str) -> str:
    data = pyproject_data(package)
    return data["project"]["version"]


def prebuilt_release_tag(package: str) -> str:
    data = pyproject_data(package)
    return data["tool"][package]["prebuilt_release_tag"]


def shared_value(values: dict[str, str], label: str) -> str:
    unique = set(values.values())
    if len(unique) != 1:
        details = ", ".join(
            f"{package}={value}" for package, value in sorted(values.items())
        )
        raise RuntimeError(f"Mismatched {label} across packages: {details}")
    return next(iter(unique))


def latest_release_version() -> str:
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    return str(payload["tag_name"]).removeprefix("llvmorg-")


def latest_prebuilt_release_tag() -> str:
    request = urllib.request.Request(
        LATEST_PREBUILT_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    return str(payload["tag_name"])


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

    package_versions = {
        package: project_version(package) for package in PACKAGE_PYPROJECTS
    }
    package_prebuilt_tags = {
        package: prebuilt_release_tag(package) for package in PACKAGE_PYPROJECTS
    }
    pinned = shared_value(package_versions, "LLVM version")
    pinned_prebuilt = shared_value(package_prebuilt_tags, "prebuilt release tag")
    latest = latest_release_version()
    latest_prebuilt = latest_prebuilt_release_tag()
    upstream = download_upstream_run_clang_tidy(pinned)
    local = LOCAL_RUN_CLANG_TIDY.read_text(encoding="utf-8")
    changed = upstream != local

    if changed and args.update:
        LOCAL_RUN_CLANG_TIDY.write_text(upstream, encoding="utf-8")

    print(f"pinned_version={pinned}")
    print(f"latest_version={latest}")
    print(f"pinned_prebuilt_release={pinned_prebuilt}")
    print(f"latest_prebuilt_release={latest_prebuilt}")
    print(f"run_clang_tidy_changed={'true' if changed else 'false'}")
    print(f"newer_llvm_available={'true' if latest != pinned else 'false'}")
    print(
        "newer_prebuilt_release_available="
        f"{'true' if latest_prebuilt != pinned_prebuilt else 'false'}"
    )

    if args.github_output is not None:
        write_github_output(
            args.github_output,
            {
                "pinned_version": pinned,
                "latest_version": latest,
                "pinned_prebuilt_release": pinned_prebuilt,
                "latest_prebuilt_release": latest_prebuilt,
                "run_clang_tidy_changed": "true" if changed else "false",
                "newer_llvm_available": "true" if latest != pinned else "false",
                "newer_prebuilt_release_available": (
                    "true" if latest_prebuilt != pinned_prebuilt else "false"
                ),
            },
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
