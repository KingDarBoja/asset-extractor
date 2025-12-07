# Asset Extractor Test Suite

This directory contains the integration test suite for the asset-extractor project.

## Overview

The test suite uses **pytest** to validate the functionality of:
- Buff UI text mapping and localization
- Asset pool flattening and probability calculations
- Automatic buff type name mapping
- UI text cache functionality
- Attribute UI properties

## Directory Structure

```
tests/
├── conftest.py              # Shared pytest fixtures (AssetCache, config, etc.)
├── integration/             # Integration tests
│   ├── test_buff_ui_pytest.py       # Buff UI tests (pytest format)
│   ├── test_pool_pytest.py          # Pool functionality tests (pytest format)
│   ├── test_mapping_pytest.py       # Mapping tests (pytest format)
│   ├── test_boost_conditions.py     # Boost condition extraction tests
│   ├── test_buff_ui_suite.py        # Original buff UI tests
│   ├── test_pool_flattening.py      # Original pool tests
│   ├── test_all_fixes.py            # Regression tests
│   └── ... (other legacy test scripts)
├── debugging/               # Standalone debugging scripts
│   ├── check_boost_conditions.py    # Check boost condition extraction
│   ├── check_items_csv.py           # Validate generated items CSV
│   └── ... (other debugging scripts)
└── README.md                # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests (simplest method)
test.cmd

# Run all tests with verbose output
test.cmd -v

# Run only buff_ui tests
test.cmd -m buff_ui

# Run only pool tests
test.cmd -m pool

# Run all tests using nox
uv run nox -s test
```

### Using pytest directly

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/integration/test_buff_ui_pytest.py

# Run boost condition tests
uv run pytest tests/integration/test_boost_conditions.py

# Run specific test class
uv run pytest tests/integration/test_buff_ui_pytest.py::TestRecruitmentUpgradeVariants

# Run specific test
uv run pytest tests/integration/test_buff_ui_pytest.py::TestRecruitmentUpgradeVariants::test_recruitment_variant_text

# Run tests matching a keyword
uv run pytest -k "recruitment"
uv run pytest -k "boost_condition"

# Run tests with specific marker
uv run pytest -m buff_ui
uv run pytest -m pool
uv run pytest -m mapping

# Exit on first failure
uv run pytest -x

# Show available markers
uv run pytest --markers
```

### Using nox

```bash
# Run tests with nox (default)
uv run nox -s test

# Run tests with verbose output
uv run nox -s test_verbose

# Show available markers
uv run nox -s test_markers

# Run tests with coverage report
uv run nox -s test_coverage
```

### Using the test runner script

```bash
# Run with default settings
uv run python run_tests.py

# Verbose output
uv run python run_tests.py -v

# Very verbose output
uv run python run_tests.py -vv

# Run only buff_ui tests
uv run python run_tests.py -m buff_ui

# Run tests matching keyword
uv run python run_tests.py -k "recruitment"

# Exit on first failure
uv run python run_tests.py -x

# List available markers
uv run python run_tests.py --list-markers

# Run specific test file
uv run python run_tests.py tests/integration/test_buff_ui_pytest.py
```

## Test Markers

The test suite uses pytest markers to categorize tests:

- **`buff_ui`** - Tests for buff UI text mapping and BuffUI creation
- **`pool`** - Tests for asset pool functionality (flattening, probabilities)
- **`mapping`** - Tests for automatic buff type name mapping and UI text cache
- **`slow`** - Tests that take longer to run (can be excluded with `-m "not slow"`)

### Running Tests by Marker

```bash
# Run only buff UI tests
uv run pytest -m buff_ui

# Run only pool tests
uv run pytest -m pool

# Run only mapping tests
uv run pytest -m mapping

# Run buff_ui AND mapping tests
uv run pytest -m "buff_ui or mapping"

# Run all except slow tests
uv run pytest -m "not slow"
```

## Test Files

### Pytest Format Tests (Recommended)

- **`test_buff_ui_pytest.py`** - Comprehensive buff UI tests
  - RecruitmentUpgrade variant text selection
  - MovementUpgrade buff type mapping
  - Buff struct text fields
  - Asset.buff_ui property
  - All regression tests

- **`test_pool_pytest.py`** - Pool functionality tests
  - Pool flattening and probability calculations
  - Nested pool handling
  - Pool structure validation

- **`test_mapping_pytest.py`** - Mapping and UI text cache tests
  - Buff type name derivation
  - Dataset literal mapping (Rarity, ItemNiche, Scope)
  - Attribute UI properties (ui_text_id, ui_icon_guid, ui_text_variants)

- **`test_boost_conditions.py`** - Boost condition extraction tests
  - Validates all ItemWithBoost assets have proper conditions
  - Tests specific condition types (NeedAttributeCounter, PlayerCounter, etc.)
  - End-to-end CSV validation
  - Ensures no generic "Boost condition active" fallbacks

### Legacy Test Scripts

The `tests/integration/` directory also contains legacy test scripts that can be run directly:

```bash
# Run individual legacy tests
uv run python tests/integration/test_all_fixes.py
uv run python tests/integration/test_pool_flattening.py
uv run python tests/integration/test_buff_ui_suite.py
```

These scripts will eventually be migrated to pytest format.

### Debugging Scripts

The `tests/debugging/` directory contains standalone scripts for quick validation and debugging:

- **`check_boost_conditions.py`** - Validate boost condition extraction
  ```bash
  uv run python tests/debugging/check_boost_conditions.py
  ```
  Checks all ItemWithBoost assets and reports:
  - Condition type statistics
  - Items with generic "Boost condition active" (errors)
  - Specific test case validation (Health >= 1000, etc.)

- **`check_items_csv.py`** - Validate generated items CSV
  ```bash
  # Check latest CSV file
  uv run python tests/debugging/check_items_csv.py

  # Check specific CSV file
  uv run python tests/debugging/check_items_csv.py results/tables/items_v5.csv
  ```
  Validates:
  - CSV structure and completeness
  - Boost condition correctness
  - Source coverage (should be >= 80%)
  - Rarity distribution
  - Price statistics

These scripts provide quick feedback without needing to run the full test suite.

## Shared Fixtures

The `conftest.py` file provides shared fixtures available to all tests:

- **`config`** - Loaded configuration (session scope)
- **`assets`** - AssetCache instance (session scope, expensive to load)
- **`ui_text_cache`** - UITextCache instance (session scope)
- **`texts`** - TextCache instance (session scope)
- **`pytest.get_english_text(text_obj)`** - Helper function to extract English text

### Using Fixtures in Tests

```python
import pytest

def test_my_feature(assets, ui_text_cache):
    """Test using shared fixtures."""
    item = assets.get(12345)
    assert item is not None

    buff_type = ui_text_cache.get_buff_type_name("FactoryUpgrade", "ProductivityUpgrade")
    assert buff_type == "BuffProductivity"
```

## Writing New Tests

### Test File Template

```python
"""Description of what this test file tests."""

import pytest


@pytest.mark.your_marker
class TestYourFeature:
    """Test class description."""

    def test_specific_behavior(self, assets):
        """Test description."""
        # Arrange
        item = assets.get(12345)

        # Act
        result = item.some_property()

        # Assert
        assert result is not None


@pytest.mark.your_marker
class TestAnotherFeature:
    """Another test class."""

    @pytest.mark.parametrize(
        "guid,expected_value",
        [
            (12345, "Expected1"),
            (67890, "Expected2"),
        ],
    )
    def test_parametrized(self, assets, guid, expected_value):
        """Test with multiple parameter sets."""
        item = assets.get(guid)
        assert item.value == expected_value
```

### Best Practices

1. **Use descriptive test names** - `test_recruitment_variant_text` not `test1`
2. **Use pytest markers** - Tag tests with appropriate markers
3. **Use parametrize** - For testing multiple similar cases
4. **Use shared fixtures** - Don't reload AssetCache in each test
5. **Add docstrings** - Explain what the test validates
6. **Use assertions with messages** - Make failures informative
7. **Skip when appropriate** - Use `pytest.skip()` for unavailable data

## Continuous Integration

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: uv run nox -s test
```

## Coverage Reports

To generate a coverage report:

```bash
# Using nox
uv run nox -s test_coverage

# Using pytest directly
uv run pytest --cov=assetextractor --cov-report=html --cov-report=term

# View HTML coverage report
start htmlcov/index.html  # Windows
```

## Troubleshooting

### Tests fail with "config.json not found"

Make sure you're running tests from the project root directory where `config.json` is located.

### Tests take a long time

The AssetCache is expensive to load. The test suite uses session-scoped fixtures to load it only once. If you're writing tests, make sure you use the `assets` fixture instead of loading AssetCache yourself.

### Import errors

Make sure the project is installed in development mode:

```bash
uv sync --dev
```

## Contributing

When adding new features to the asset-extractor:

1. Write tests first (TDD approach)
2. Add tests to the appropriate test file (or create a new one)
3. Use appropriate markers
4. Ensure all tests pass before committing
5. Run the full test suite: `uv run nox -s test`

## Questions?

See the main project documentation in `CLAUDE.md` and `AGENTS.md`.
