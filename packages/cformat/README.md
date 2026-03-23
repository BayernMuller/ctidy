# cformat

`cformat` packages a prebuilt `clang-format` binary into a Python wheel so the tool can be invoked with:

```bash
cformat
uv run cformat
```

The package always uses the bundled binary. It never falls back to a system `clang-format`.

`cformat` does not build LLVM in this repository. During wheel builds it only:

- downloads pinned prebuilt static binaries from `muttleyxd/clang-tools-static-binaries`
- verifies their `.sha512sum` files

PyPI releases are wheel-only for now. `cformat` does not publish an `sdist`.

Supported wheel platforms are limited to the LLVM 20 assets that exist in the pinned prebuilt release:

- Linux `x86_64`
- macOS `x86_64`
- macOS `arm64`
- Windows `x86_64`
