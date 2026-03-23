# ctidy

`ctidy` packages `clang-tidy`, `clang-apply-replacements`, LLVM resource headers, and a bundled `run-clang-tidy.py` into a Python wheel.

Use it when you want a reproducible `clang-tidy` setup from Python packaging without depending on a system LLVM install.

## What Gets Installed

`ctidy` always runs the bundled tools:

- `clang-tidy`
- `clang-apply-replacements`
- `run-clang-tidy.py`
- `lib/clang/<major>/include` resource headers

It never falls back to a system `clang-tidy`.

## Installation

Recommended for project environments: `uv`

```bash
uv add ctidy
```

Recommended for one-off runs: `uvx`

```bash
uvx ctidy --version
uvx ctidy -p build --checks='modernize-*' src/foo.cc
```

You can also install with `pip`:

```bash
pip install ctidy
```

The examples below assume your virtual environment is already activated, so you can invoke `ctidy` directly.

Check that the wrapper is available:

```bash
ctidy --version
```

## Requirements

`ctidy` expects a compilation database. In practice that means your project needs a `compile_commands.json`.

For CMake projects:

```bash
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

After that, run `ctidy` from the project root or pass `-p <build-dir>` explicitly.

## How It Resolves The Build Directory

If you do not pass `-p` or `--build-path`, `ctidy` automatically looks for `compile_commands.json` in these locations relative to the current working directory:

- `build/compile_commands.json`
- `.build/compile_commands.json`
- `out/build/compile_commands.json`
- `compile_commands.json`

If none of them exist, `ctidy` exits with an error and asks you to provide `-p <build-dir>`.

## Basic Usage

Run a check on one file:

```bash
ctidy src/foo.cc
```

Run with an explicit build directory:

```bash
ctidy -p build src/foo.cc
```

Run only selected checks:

```bash
ctidy -p build --checks='modernize-*,performance-*' src/foo.cc
```

Apply fixes:

```bash
ctidy -p build --fix src/foo.cc
```

Run across the whole project with multiple jobs:

```bash
ctidy -p build -j 8
```

Restrict diagnostics to project headers:

```bash
ctidy -p build --header-filter='^(src|include)/' src/foo.cc
```

## Argument Forwarding

`ctidy` is a wrapper around the bundled LLVM `run-clang-tidy.py`. Aside from `--version` and build-path auto-discovery, CLI arguments are forwarded to that runner.

Use the upstream help output to inspect available flags:

```bash
ctidy --help
```

## Typical Workflow

A common project flow looks like this:

```bash
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
uv add ctidy
ctidy -p build --checks='bugprone-*,modernize-*' -j 8
ctidy -p build --fix src/foo.cc
```

## Packaging Notes

`ctidy` does not build LLVM in this repository. During wheel builds it only:

- downloads pinned prebuilt static binaries from `muttleyxd/clang-tools-static-binaries`
- verifies their `.sha512sum` files
- downloads official LLVM release headers for `lib/clang/<major>/include`
- bundles the upstream LLVM `run-clang-tidy.py`

PyPI releases are wheel-only. `ctidy` does not publish an `sdist`.

Supported wheel platforms are limited to the LLVM 20 assets available in the pinned prebuilt release:

- Linux `x86_64`
- macOS `x86_64`
- macOS `arm64`
- Windows `x86_64`

If the upstream static build release does not publish an asset for your OS/CPU pair, `ctidy` does not build a wheel for that platform.
