from __future__ import annotations

import os
import re
import shutil
import stat
import tarfile
import urllib.request
from pathlib import Path
from platform import machine, system

from setuptools.command.build_py import build_py as _build_py
from setuptools.errors import SetupError

try:
    from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
except ModuleNotFoundError:  # pragma: no cover
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
RUN_CLANG_TIDY = ROOT / "src/ctidy/data/bin/run-clang-tidy.py"


def pyproject_data() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def project_version() -> str:
    return str(pyproject_data()["project"]["version"])


def llvm_major_version() -> str:
    return project_version().split(".", 1)[0]


def prebuilt_release_tag() -> str:
    return str(pyproject_data()["tool"]["ctidy"]["prebuilt_release_tag"])


def download_root() -> Path:
    configured = (
        os.environ.get("CTIDY_DOWNLOAD_DIR")
        or os.environ.get("CTIDY_LLVM_DOWNLOAD_DIR")
        or str(ROOT / ".cache" / "ctidy-downloads")
    )
    return Path(configured).resolve()


def llvm_archive_path() -> Path:
    return (
        download_root()
        / prebuilt_release_tag()
        / f"llvm-project-{project_version()}.src.tar.xz"
    )


def current_platform() -> tuple[str, str]:
    host_system = system()
    host_machine = machine().lower()

    if host_system == "Linux" and host_machine in {"x86_64", "amd64"}:
        return "linux-amd64", ""
    if host_system == "Darwin" and host_machine in {"x86_64", "amd64"}:
        return "macosx-amd64", ""
    if host_system == "Darwin" and host_machine in {"arm64", "aarch64"}:
        return "macos-arm-arm64", ""
    if host_system == "Windows" and host_machine in {"amd64", "x86_64"}:
        return "windows-amd64", ".exe"

    raise SetupError(
        "ctidy does not have a bundled clang-tidy asset for "
        f"{host_system}/{host_machine}."
    )


def asset_name(stem: str) -> str:
    platform_name, suffix = current_platform()
    return f"{stem}-{llvm_major_version()}_{platform_name}{suffix}"


def cached_download(url: str, destination: Path) -> Path:
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
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


def download_prebuilt_asset(stem: str) -> Path:
    release_tag = prebuilt_release_tag()
    asset = asset_name(stem)
    asset_path = download_root() / release_tag / asset
    base_url = (
        "https://github.com/muttleyxd/clang-tools-static-binaries/releases/download/"
        f"{release_tag}/{asset}"
    )
    hash_path = asset_path.with_name(f"{asset}.sha512sum")

    cached_download(base_url, asset_path)
    cached_download(f"{base_url}.sha512sum", hash_path)

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


def extract_resource_headers(destination: Path) -> None:
    version = project_version()
    archive = llvm_archive_path()
    url = (
        "https://github.com/llvm/llvm-project/releases/download/"
        f"llvmorg-{version}/llvm-project-{version}.src.tar.xz"
    )
    cached_download(url, archive)

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


def stage_ctidy_payload(build_lib: Path) -> None:
    _, executable_suffix = current_platform()
    package_root = build_lib / "ctidy"
    bin_dir = package_root / "data" / "bin"
    include_dir = (
        package_root / "data" / "lib" / "clang" / llvm_major_version() / "include"
    )

    bin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUN_CLANG_TIDY, bin_dir / "run-clang-tidy.py")

    copy_executable(
        download_prebuilt_asset("clang-tidy"),
        bin_dir / f"clang-tidy{executable_suffix}",
    )
    copy_executable(
        download_prebuilt_asset("clang-apply-replacements"),
        bin_dir / f"clang-apply-replacements{executable_suffix}",
    )
    extract_resource_headers(include_dir)


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        stage_ctidy_payload(Path(self.build_lib))


class bdist_wheel(_bdist_wheel):
    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self) -> tuple[str, str, str]:
        _, _, platform_tag = super().get_tag()
        return "py3", "none", platform_tag
