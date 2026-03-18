# ctidy

`ctidy` packages `clang-tidy`, `clang-apply-replacements`, resource headers, and a bundled `run-clang-tidy.py` into a Python wheel so the tool can be invoked with:

```bash
ctidy
uv run ctidy
```

The package always uses the bundled binaries. It never falls back to a system `clang-tidy`.

