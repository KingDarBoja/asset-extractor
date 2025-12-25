# Building Size Verification Test

## Overview

The `verify_building_sizes.py` test compares building sizes calculated from IFO files against expected values from the `demo_record_building_calculation.csv` file.

## Purpose

This test validates that the building size extraction logic in `conversion/calculator/building-sizes.py` correctly:
1. Parses IFO files to extract building footprint dimensions
2. Calculates building sizes (width x height) in grid cells
3. Matches the expected sizes documented in the CSV

## Test Structure

### Test Functions

1. **`test_csv_loading()`** - Verifies the CSV can be loaded and parsed correctly
2. **`test_building_sizes()`** - Main test that compares calculated vs expected building sizes
3. **`test_building_size_parsing_errors()`** - Summarizes parsing errors and size determination failures

### What It Tests

- **CSV Parsing**: Loads expected building sizes from the demo CSV file (47 buildings)
- **Size Calculation**: Runs the building-sizes.py converter to calculate sizes from IFO files
- **Comparison**: Compares calculated sizes with expected values and reports:
  - Missing buildings (not found in assets or no calculated size)
  - Size mismatches (calculated size differs from expected)
  - Matching buildings count (shows X/47 matches)
- **Parsing Errors**: Captures and summarizes errors during IFO file parsing:
  - Size determination failures (defaulted to 1x1)
  - IFO parsing errors

## Running the Tests

### Run all building size tests:
```bash
uv run python run_tests.py tests/integration/verify_building_sizes.py -v
```

### Run just the CSV loading test:
```bash
uv run python run_tests.py tests/integration/verify_building_sizes.py::test_csv_loading -v
```

### Run the full comparison test:
```bash
uv run python run_tests.py tests/integration/verify_building_sizes.py::test_building_sizes -v -s
```

### Run the parsing error summary test:
```bash
uv run python run_tests.py tests/integration/verify_building_sizes.py::test_building_size_parsing_errors -v -s
```

**Note**: Use `-s` flag to see detailed output during the test execution.

## Expected Behavior

### On Success
The test passes when all building sizes match expected values. Output shows:
```
Total buildings in CSV: 47
Total buildings calculated: XXX

✓ Matching building sizes: 47/47
✗ Total differences: 0/47
```

**Note**: The test only compares the 47 buildings in the CSV. Additional buildings in the calculated output are ignored.

### On Failure
The test fails and shows:
- Summary of differences (missing buildings and size mismatches)
- Sample differences for inspection
- Path to detailed report: `results/test_reports/building_size_differences.txt`

### Sample Output - Comparison Test
```
BUILDING SIZE VERIFICATION RESULTS
================================================================================

Total buildings in CSV: 47
Total buildings calculated: 450

✓ Matching building sizes: 44/47
✗ Total differences: 3/47

Missing buildings: 1
  - Unknown Building: expected (5, 5)

Size mismatches: 2
  - Oats: expected (4, 4), got (4, 5)
  - Market: expected (5, 6), got (6, 5)

Detailed report saved to: results\test_reports\building_size_differences.txt
```

### Sample Output - Parsing Errors Test
```
BUILDING SIZE PARSING ERROR SUMMARY
================================================================================

Total buildings processed: 450
Size determination errors: 25
IFO parsing errors: 2
Total errors: 27

--------------------------------------------------------------------------------
SIZE DETERMINATION ERRORS (defaulted to 1x1):
--------------------------------------------------------------------------------
  Asset ID 12345 (Ornament_Small): Size could not be determined
  Asset ID 12346 (Field_Small): Size could not be determined
  ... and 23 more

--------------------------------------------------------------------------------
IFO PARSING ERRORS:
--------------------------------------------------------------------------------
  Error parsing IFO file C:\path\to\file.ifo: Invalid XML
  ... and 1 more

Detailed error report saved to: results\test_reports\building_size_parsing_errors.txt

✓ Parsing errors summary complete
```

## CSV File Format

The test expects `tests/integration/demo_record_building_calculation.csv` with:
- **Column 1**: Building name (English)
- **Column 8**: Short side (width)
- **Column 9**: Long side (height)

The test automatically:
- Skips header rows and empty rows
- Handles UTF-8 with BOM encoding
- Filters out invalid or incomplete data

## Files Generated

- **`building-sizes.json`**: JSON file with calculated sizes (GUID → [width, height])
- **`results/test_reports/building_size_differences.txt`**: Detailed report of size comparison differences
- **`results/test_reports/building_size_parsing_errors.txt`**: Detailed report of parsing errors and failures

## Implementation Details

### How Building Sizes Are Calculated

The converter (`building-sizes.py`) calculates sizes by:
1. Finding the IFO file for each building asset
2. Parsing BuildBlocker corner positions from the IFO XML
3. Computing the bounding box dimensions
4. Rounding to nearest grid cells

### How Buildings Are Matched

The test matches buildings by:
1. Loading expected sizes keyed by building name
2. Finding the GUID for each building name in the asset cache
3. Looking up the calculated size for that GUID
4. Comparing the tuples (width, height)

### Special Cases

- **1x1 Buildings**: Fields and ornaments often default to (1, 1) when IFO parsing fails
- **Multi-blocker Buildings**: Mines with multiple blockers use the first/smallest blocker
- **Missing Assets**: Buildings not found in the asset cache are reported as missing

## Troubleshooting

### "CSV file not found"
Ensure `tests/integration/demo_record_building_calculation.csv` exists.

### "Generated JSON not found"
The converter automatically generates `building-sizes.json` when the test runs. If you see this error, check that the converter ran successfully.

### Import errors
The test dynamically imports `building-sizes.py` (hyphenated filename) using `importlib`. If you see import errors, verify the script exists at:
```
assetextractor/conversion/calculator/building-sizes.py
```

### Many size mismatches
This could indicate:
- IFO files have changed (game update)
- CSV has outdated data
- Building size calculation logic needs adjustment

## Future Improvements

Potential enhancements:
- [ ] Add building GUID column to CSV for direct matching (avoid name lookups)
- [ ] Support for diagonal building sizes
- [ ] Automatic CSV update when sizes change
- [ ] Visual diff report showing building footprints
- [ ] Integration with version tracking system
