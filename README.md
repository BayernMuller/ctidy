# ctidy

`ctidy` packages `clang-tidy`, `clang-apply-replacements`, resource headers, and a bundled `run-clang-tidy.py` into a Python wheel so the tool can be invoked with:

```bash
ctidy
uv run ctidy
```

The package always uses the bundled binaries. It never falls back to a system `clang-tidy`.

The wheel keeps the upstream LLVM `run-clang-tidy.py`, downloads official LLVM release headers for `lib/clang/<major>/include`, and packages prebuilt `clang-tidy` binaries from `muttleyxd/clang-tools-static-binaries` during the Python wheel build.
