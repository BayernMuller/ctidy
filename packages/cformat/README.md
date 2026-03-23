# cformat

`cformat` packages a prebuilt `clang-format` binary into a Python wheel.

Use it when you want to format C/C++ sources from a Python-managed environment without relying on a system LLVM install.

## What Gets Installed

`cformat` always runs the bundled `clang-format` binary. It never falls back to a system `clang-format`.

## Installation

Recommended for project environments: `uv`

```bash
uv add cformat
```

Recommended for one-off runs: `uvx`

```bash
uvx cformat --version
uvx cformat -i --style=file src/foo.cc
```

You can also install with `pip`:

```bash
pip install cformat
```

The examples below assume your virtual environment is already activated, so you can invoke `cformat` directly.

Check that the wrapper is available:

```bash
cformat --version
```

## Basic Usage

Format a file in place:

```bash
cformat -i src/foo.cc
```

Format multiple files in place:

```bash
cformat -i src/foo.cc src/bar.cc include/foo.hpp
```

Print formatted output to stdout:

```bash
cformat src/foo.cc
```

Use the style from your `.clang-format` file:

```bash
cformat -i --style=file src/foo.cc
```

Format code passed on stdin:

```bash
cat src/foo.cc | cformat --assume-filename=src/foo.cc
```

## Argument Forwarding

`cformat` is a thin wrapper around the bundled `clang-format` binary. Aside from `--version`, CLI arguments are forwarded directly to `clang-format`.

Use the upstream help output to inspect available flags:

```bash
cformat --help
```

## Typical Workflow

Common formatting commands:

```bash
uv add cformat
cformat -i --style=file src/foo.cc include/foo.hpp
cformat --dry-run -Werror src/foo.cc include/foo.hpp
```

The last command is useful in CI when you want formatting mismatches to fail the build.

## Packaging Notes

`cformat` does not build LLVM in this repository. During wheel builds it only:

- downloads pinned prebuilt static binaries from `muttleyxd/clang-tools-static-binaries`
- verifies their `.sha512sum` files

PyPI releases are wheel-only. `cformat` does not publish an `sdist`.

Supported wheel platforms are limited to the LLVM 20 assets available in the pinned prebuilt release:

- Linux `x86_64`
- macOS `x86_64`
- macOS `arm64`
- Windows `x86_64`

If the upstream static build release does not publish an asset for your OS/CPU pair, `cformat` does not build a wheel for that platform.
