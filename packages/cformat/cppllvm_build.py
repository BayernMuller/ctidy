from __future__ import annotations

# Vendored copy of /cppllvm_build.py.
# This file stays package-local so `packages/cformat` can build in isolation.

import os
import re
import shutil
import stat
import sys
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from platform import machine, system

from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
from setuptools.command.build_py import build_py as _build_py
from setuptools.errors import SetupError

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


SUPPORTED_PREBUILT_PLATFORMS: dict[tuple[str, str], tuple[str, str]] = {
    ("Linux", "x86_64"): ("linux-amd64", ""),
    ("Linux", "amd64"): ("linux-amd64", ""),
    ("Darwin", "x86_64"): ("macosx-amd64", ""),
    ("Darwin", "amd64"): ("macosx-amd64", ""),
    ("Darwin", "arm64"): ("macos-arm-arm64", ""),
    ("Darwin", "aarch64"): ("macos-arm-arm64", ""),
    ("Windows", "x86_64"): ("windows-amd64", ".exe"),
    ("Windows", "amd64"): ("windows-amd64", ".exe"),
}


@dataclass(frozen=True)
class PackageBuildConfig:
    package_dir: Path
    package_name: str
    tool_section: str
    binaries: tuple[str, ...]
    copied_files: tuple[tuple[Path, str], ...] = ()
    include_resource_headers: bool = False
    download_env_vars: tuple[str, ...] = ()


def pyproject_data(config: PackageBuildConfig) -> dict:
    pyproject = config.package_dir / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def project_version(config: PackageBuildConfig) -> str:
    return str(pyproject_data(config)["project"]["version"])


def llvm_major_version(config: PackageBuildConfig) -> str:
    return project_version(config).split(".", 1)[0]


def prebuilt_release_tag(config: PackageBuildConfig) -> str:
    return str(
        pyproject_data(config)["tool"][config.tool_section]["prebuilt_release_tag"]
    )


def download_root(config: PackageBuildConfig) -> Path:
    for env_var in ("CPPLLVM_DOWNLOAD_DIR", *config.download_env_vars):
        value = os.environ.get(env_var)
        if value:
            return Path(value).resolve()
    return (
        config.package_dir / ".cache" / f"{config.package_name}-downloads"
    ).resolve()


def llvm_archive_path(config: PackageBuildConfig) -> Path:
    return (
        download_root(config)
        / prebuilt_release_tag(config)
        / f"llvm-project-{project_version(config)}.src.tar.xz"
    )


def supported_platform_labels() -> str:
    return ", ".join(
        [
            "Linux/x86_64",
            "macOS/x86_64",
            "macOS/arm64",
            "Windows/x86_64",
        ]
    )


def current_platform(config: PackageBuildConfig) -> tuple[str, str]:
    host_system = system()
    host_machine = machine().lower()

    platform_spec = SUPPORTED_PREBUILT_PLATFORMS.get((host_system, host_machine))
    if platform_spec is None:
        raise SetupError(
            f"{config.package_name} only publishes wheels for platforms with pinned "
            "prebuilt static binaries from muttleyxd/clang-tools-static-binaries. "
            f"Supported platforms for LLVM {llvm_major_version(config)}: "
            f"{supported_platform_labels()}. "
            f"Got {host_system}/{host_machine}."
        )
    return platform_spec


def asset_name(config: PackageBuildConfig, stem: str) -> str:
    platform_name, suffix = current_platform(config)
    return f"{stem}-{llvm_major_version(config)}_{platform_name}{suffix}"


def cached_download(url: str, destination: Path, *, package_name: str) -> Path:
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"{package_name}-build-hooks"},
    )
    with urllib.request.urlopen(request) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def read_expected_sha512(path: Path) -> str:
    content = path.read_text(encoding="utf-8").strip()
    match = re.match(r"(?P<hash>[0-9A-Fa-f]+)", content)
    if match is None:
        raise SetupError(f"Could not parse SHA-512 from {path}.")
    return match.group("hash").lower()


def sha512(path: Path) -> str:
    import hashlib

    digest = hashlib.sha512()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def download_prebuilt_asset(config: PackageBuildConfig, stem: str) -> Path:
    release_tag = prebuilt_release_tag(config)
    asset = asset_name(config, stem)
    asset_path = download_root(config) / release_tag / asset
    base_url = (
        "https://github.com/muttleyxd/clang-tools-static-binaries/releases/download/"
        f"{release_tag}/{asset}"
    )
    hash_path = asset_path.with_name(f"{asset}.sha512sum")

    cached_download(base_url, asset_path, package_name=config.package_name)
    cached_download(
        f"{base_url}.sha512sum",
        hash_path,
        package_name=config.package_name,
    )

    expected = read_expected_sha512(hash_path)
    actual = sha512(asset_path)
    if actual != expected:
        raise SetupError(
            f"SHA-512 mismatch for {asset}: expected {expected}, got {actual}."
        )

    return asset_path


def copy_executable(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    destination.chmod(
        destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def extract_resource_headers(config: PackageBuildConfig, destination: Path) -> None:
    version = project_version(config)
    archive = llvm_archive_path(config)
    url = (
        "https://github.com/llvm/llvm-project/releases/download/"
        f"llvmorg-{version}/llvm-project-{version}.src.tar.xz"
    )
    cached_download(url, archive, package_name=config.package_name)

    prefix = f"llvm-project-{version}.src/clang/lib/Headers/"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, mode="r:xz") as tar:
        for member in tar.getmembers():
            if not member.name.startswith(prefix):
                continue
            relative = member.name[len(prefix) :]
            if not relative or relative == "CMakeLists.txt":
                continue

            output = destination / relative
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
                continue

            output.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            with extracted, output.open("wb") as handle:
                shutil.copyfileobj(extracted, handle)


def stage_payload(config: PackageBuildConfig, build_lib: Path) -> None:
    _, executable_suffix = current_platform(config)
    package_root = build_lib / config.package_name
    data_root = package_root / "data"
    bin_dir = data_root / "bin"

    for source, relative_destination in config.copied_files:
        destination = data_root / relative_destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for stem in config.binaries:
        copy_executable(
            download_prebuilt_asset(config, stem),
            bin_dir / f"{stem}{executable_suffix}",
        )

    if config.include_resource_headers:
        extract_resource_headers(
            config,
            data_root / "lib" / "clang" / llvm_major_version(config) / "include",
        )


def make_build_commands(
    config: PackageBuildConfig,
) -> tuple[type[_build_py], type[_bdist_wheel]]:
    class build_py(_build_py):
        def run(self) -> None:
            super().run()
            stage_payload(config, Path(self.build_lib))

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self) -> None:
            super().finalize_options()
            self.root_is_pure = False

        def get_tag(self) -> tuple[str, str, str]:
            _, _, platform_tag = super().get_tag()
            return "py3", "none", platform_tag

    return build_py, bdist_wheel
