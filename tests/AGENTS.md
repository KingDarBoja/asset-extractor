# Test Conventions

The project uses **pytest** for integration testing.

## Layout

- `tests/integration/` — permanent test cases verifying correct output. New tests for any implemented feature belong here.
- `tests/debugging/` — throwaway scripts that probe program behaviour during investigation. Place exploratory scripts here.
- `tests/conftest.py` — shared fixtures: `assets`, `config`, `ui_text_cache`, `texts`. Reuse them in new tests.
- `tests/README.md` — comprehensive testing guide.

## Authoring

- Follow pytest conventions (`test_*` functions, assertions over prints).
- Use the shared fixtures rather than re-loading assets inside tests.
- After implementing a feature, promote any debugging script that verifies correct output into `tests/integration/` as a permanent test case.

## Running

```bash
test.cmd                 # all tests
uv run pytest            # equivalent
uv run pytest -v
uv run pytest -k <expr>
uv run pytest -m <mark>  # markers: buff_ui, pool, mapping, ...
```

See `docs/development.md` for the full command list.
