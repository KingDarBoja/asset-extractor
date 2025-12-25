# Fix pyright errors

1. Run `uv run nox -s pyright`. Limit the output you read.
2. If there are many errors, identify the most frequent ones and group them by cause.
3. Add strict type annotations to all methods with `partially unknown` . Never use "t.Any" except for "Attribute[t.Any, t.Any]"! Test for subclasses of attribute using isinstance rather than individual members!
4. Create data classes instead of dicts.
5. Rerun until all errors are fixed.