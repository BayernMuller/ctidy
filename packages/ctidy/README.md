# ctidy

`ctidy` packages `clang-tidy`, `clang-apply-replacements`, resource headers, and a bundled `run-clang-tidy.py` into a Python wheel so the tool can be invoked with:

```bash
ctidy
uv run ctidy
```

The package always uses the bundled binaries. It never falls back to a system `clang-tidy`.

`ctidy` does not build LLVM in this repository. During wheel builds it only:

- downloads pinned prebuilt static binaries from `muttleyxd/clang-tools-static-binaries`
- verifies their `.sha512sum` files
- downloads official LLVM release headers for `lib/clang/<major>/include`
- bundles the upstream LLVM `run-clang-tidy.py`

PyPI releases are wheel-only for now. `ctidy` does not publish an `sdist`.

Supported wheel platforms are limited to the LLVM 20 assets that exist in the pinned prebuilt release:

- Linux `x86_64`
- macOS `x86_64`
- macOS `arm64`
- Windows `x86_64`

If the upstream static build release does not publish an asset for your OS/CPU pair, `ctidy` will not build a wheel for that platform.
