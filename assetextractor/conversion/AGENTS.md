# Asset Conversion Module Guide

@../../AGENTS.md

This guide documents specific implementation details for the asset conversion module.

## Building Size Calculator

### Overview

The building size calculator (`calculator/building-sizes.py`) extracts building footprint dimensions from Anno 117 game files (.ifo files) and exports them to JSON format.

**Location**: `assetextractor/conversion/calculator/building-sizes.py`

**Output**: `building-sizes.json` - Maps building GUIDs to (width, height) tuples

### Running the Calculator

```bash
# Always run as a module from project root
uv run python -m assetextractor.conversion.calculator.building-sizes
```

**Important**: Never run as a file path (`python assetextractor/conversion/calculator/building-sizes.py`) - this will fail with `ModuleNotFoundError`.

### IFO File Resolution Strategy

The calculator uses a 5-level priority system to find IFO files for buildings:

1. **Object.Variations[0].Filename** - Standard buildings (most common)
2. **MeshGraphStyle.AdditionalConfigs[0].ConfigFile** - Gates, hedges, decorative elements
3. **Wall.TileSetCfgFolder / Aqueduct.TileSetCfgFolder** - Modular structures (returns folder path)
4. **MeshGraphEdgeSelection.HitBoxReferenceCfg** - Reference buildings
5. **Polygon.Path** - Fallback glob pattern search

**Critical**: Each priority level checks if the file/folder exists before returning. If not found, it falls through to the next priority level.

### Size Extraction Strategies

For each IFO file, the calculator tries multiple strategies in order:

1. **BuildBlocker/Position corners** - Calculates size from 4+ corner coordinates (most accurate)
2. **BoundingBox/Extents** - Uses xf/zf dimensions (less reliable, may be in physical units not grid cells)
3. **Filename pattern** - Extracts from patterns like "04x04", "1x1" in filename
4. **Asset name pattern** - Extracts from asset names like "Ornament Celtic Statue 1x1 Obelisk"

### Special Cases

#### Custom Hardcoded Sizes

Some building types don't parse well from IFO files and use hardcoded sizes:

- **MilitaryGate template**: Always returns (1, 3) regardless of IFO data

Add more custom rules in `get_custom_size_for_special_buildings()` method.

#### Modular Infrastructure

Buildings like walls, aqueducts, and fields don't have traditional sizes. These are detected and silently default to (1, 1) without logging errors:

- Templates: `Wall`, `Aqueduct`, `Field`, `MilitaryWall`
- Keywords in name: "wall", "aqueduct", "field"

#### Exclusion Filters

Assets are excluded if they match any of these criteria (case-insensitive):

- Keywords: "test", "dummy", "preview", "placeholder", "todelete", "press_version", "debug"
- Template: `MeshGraphHealthDummy`

### Error Handling

The calculator categorizes errors into three types:

1. **IFO_NOT_FOUND** - No IFO path could be resolved from asset
2. **IFO_PARSE_ERROR** - IFO file exists but failed to parse (malformed XML, missing data)
3. **NO_SIZE_DATA** - Folder exists but contains no valid IFO files

**Error Reduction**: The implementation reduced errors from 77 to 13 (83% reduction) through:
- Multi-level IFO path resolution
- Multiple size extraction fallbacks
- Asset name pattern extraction
- Modular infrastructure detection

### Common Pitfalls

1. **Gate IFO Files**: Gates often have multiple IFO files (e.g., `gate_wood_01.ifo` and `gate_wood_doors_01.ifo`). The main file may only have BoundingBox data, while the doors file has BuildBlocker data. Solution: Use custom hardcoded size for `MilitaryGate` template.

2. **BoundingBox Dimensions**: BoundingBox/Extents values are in physical units (meters), not grid cells. Small values (< 0.5) round to 0, creating invalid sizes like (0, 0), (0, 1), or (1, 0). **Fixed**: The code now detects when either dimension is 0 after rounding BoundingBox values and falls through to filename pattern extraction and asset name extraction. Walls and fields are treated as modular infrastructure and default to 1x1. Ornaments with "1x1" in their name extract size from the name pattern.

3. **File Existence**: `Object.Variations` may point to non-existent files. Solution: Verify file exists before returning path, allow fallthrough to next priority.

4. **Modular Buildings**: Walls/aqueducts reference folders via `TileSetCfgFolder`. Solution: Handle both file and folder paths in `process_assets()`.

### Testing

**Integration test**: `tests/integration/verify_building_sizes.py::test_building_size_parsing_errors`

The test runs the converter and validates:
- Total error count is acceptable (< 15)
- Errors are categorized correctly
- Report is saved to `results/test_reports/building_size_parsing_errors.txt`

**CSV validation test**: `tests/integration/verify_building_sizes.py::test_csv_loading`

Validates building sizes against expected values from CSV reference file.
