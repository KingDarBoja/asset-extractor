# Implementation Notes

## Key Concepts

- **Asset Resolution** — the parser resolves all inheritance, so `asset.print_tree()` prints the complete resolved definition.
- **Meta Definitions** — every attribute has metadata in `properties-toolone.xml` defining data types and constraints.
- **Datasets** — ordered collections of string literals (enum-like) referenced by some attributes.
- **GUID System** — assets are identified by unique GUIDs at `Values/Standard/GUID`.

## RDA Extraction

- Uses `RDAConsole.exe` via subprocess.
- Subprocess invocation must use `shell=True` with `CREATE_NEW_CONSOLE` to avoid console-handle errors.
- Extraction strategy:
  - All files from `config.rda`
  - Icon files from `ui.rda` (filter `.*icon.*`)
  - `.ifo` files from `graphics_*.rda` (filter `.*\.ifo$`)

## Attribute Parsing Pitfalls

- **ReferenceAttribute recursion** — never iterate `ReferenceAttribute` inside recursive walkers; cycles cause infinite loops. Track visited GUIDs.
- **FileNameAttribute path resolution** — DDS/image lookup includes fallbacks across alternate subfolders; do not reimplement the path logic.
- **Boolean parsing** — Anno's boolean representations are non-standard; use `parse_bool()` from `attributes.py`.
- **FloatOrPercental** — values may be raw floats or percentages depending on context; check `is_percental` before formatting.

## Asset Iteration Patterns

- **Safe iteration** — copy to a list before iterating: `list(assets)` / `list(assets.templates)` (see `convert.py`). The cache may mutate during inheritance/reference resolution.
- **AssetCache** — unified access to assets and templates; prefer it over scanning template groups directly.
- **Inspecting assets** — `asset.print_tree()` shows the fully resolved inheritance chain.
