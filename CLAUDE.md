# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Asset Extractor is a modular Python library for reading Anno game `assets.xml` files, resolving dependencies, and converting them into legible formats. It supports localization and icon conversion for Anno 117.

## Architecture

The project is organized into three main modules under `assetextractor/`:

### 1. Extraction (`assetextractor/extraction/`)
- **Purpose**: Opens RDA files and extracts XML, DDS, CFG files to cache directory
- **Key Files**:
  - `utils.py` (Config class for managing paths)
  - `extract.py` (Dynamic RDA extraction using RDAConsole.exe)
- **Status**: Implemented with automated extraction workflow

### 2. Parsing (`assetextractor/parsing/core/`)
- **Purpose**: Reads XML files and reconstructs their hierarchical structure in memory
- **Core Components**:
  - **Templates** (`templates.py`): Define asset structure (like OOP classes)
  - **Assets** (`assets.py`): Concrete instances with resolved inheritance
  - **Properties** (`properties.py`): Building blocks of assets with nested structure
  - **Attributes** (`attributes.py`): Contain concrete values with type definitions
  - **Common** (`common.py`): Base classes and shared functionality
  - **Texts** (`texts.py`): Localization support
  - **UIText** (`uitext.py`): UI text mapping system for buff attributes

### 3. Conversion (`assetextractor/conversion/`)
- **Purpose**: Generate excerpts in different formats (HTML, JSON)
- **Asset Browser** (`assetbrowser/`): HTML converter using Jinja2 templates
  - Outputs to `config.assetbrowser_dir` (configurable in config.json)
  - Requires `Config` object passed to `Converter` constructor
- **Statistics** (`statistics/`): Item extraction and Google Sheets export
- **Status**: Fully implemented

### 4. Versioning (`assetextractor/versioning/`)
- **Purpose**: Track asset changes across game versions using SQLite database
- **Key Features**:
  - Create version snapshots with XML hash tracking
  - Compare versions to detect added/changed/deleted assets
  - Export version data to CSV/JSON
  - Query version history with statistics
- **Database**: Stores in `versioning/anno117/assets.db`
- **Status**: Fully implemented

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Install with Jupyter support
uv sync --extra jupyter
```

### Code Quality
```bash
# Run all checks (formatting, linting, type checking, tests)
uv run nox

# Format code and fix issues
uv run nox -s format_fix

# Type checking only
uv run nox -s pyright

# Manual ruff commands
uv run ruff format .
uv run ruff check . --fix
```

### Testing
```bash
# Run all tests
test.cmd
# Or: uv run nox -s test
# Or: uv run pytest

# Run with verbose output
test.cmd -v

# Run specific test category
test.cmd -m buff_ui    # Buff UI tests only
test.cmd -m pool       # Pool tests only
test.cmd -m mapping    # Mapping tests only

# Run tests matching keyword
test.cmd -k "recruitment"

# Exit on first failure
test.cmd -x

# See all testing options
test.cmd --help
# Or: see tests/README.md for comprehensive testing guide
```

### Running the Project
```bash
# Extract RDA files (run after game updates)
extract.cmd
# Or manually: uv run python -m assetextractor.extraction.extract

# Generate asset browser only
uv run python main.py

# Generate asset browser + create version snapshot + generate version report
uv run python main.py --version "1.0.1"

# Automated release build (extract, generate, snapshot, archive, export to Google Sheets)
new_version.bat
```

### Asset Versioning
```bash
# Create version snapshot (standalone)
uv run python -m assetextractor.versioning snapshot "1.0.0" --description "Launch version"

# Create snapshot during asset browser generation (recommended - loads assets only once)
uv run python main.py --version "1.0.1"

# Generate HTML version report
uv run python -m assetextractor.versioning report "1.0.0" "1.0.1" --output results/assetbrowser/

# Compare two versions
uv run python -m assetextractor.versioning diff "1.0.0" "1.0.1"

# Export version data to CSV/JSON
uv run python -m assetextractor.versioning export --output versions.csv

# Show version history
uv run python -m assetextractor.versioning history --verbose

# Get help for any command
uv run python -m assetextractor.versioning [command] --help
```

## Configuration

- **config.json**: Contains:
  - `game_path`: Anno installation directory
  - `cache_path`: Extracted files location (cache directory)
  - `assetbrowser_dir`: Output directory for asset browser HTML files
- **config.template.json**: Template for configuration setup
- All paths can be relative (resolved from config.json location) or absolute

## Key Concepts

- **Asset Resolution**: The parser resolves all inheritance so `print_tree()` shows complete asset definitions
- **Meta Definitions**: Each attribute has metadata in `properties-toolone.xml` defining data types and constraints
- **Datasets**: Ordered collections of string literals (like enums) referenced by certain attributes
- **GUID System**: Assets are identified by unique GUIDs found in `Values/Standard/GUID`

## Release Workflow

### Automated Release Build (`new_version.bat`)

The `new_version.bat` script automates the complete release process:

1. **Prompts for version number** (e.g., "1.0.1")
2. **Extracts RDA files** from game using `extract.cmd`
3. **Generates asset browser** and creates snapshot using `main.py --version`
4. **Creates 7z archive** with LZMA2 compression (1GB dict, level 7)
   - Archive name: `assetbrowser-YYYY-MM-DD.7z`
   - Source: `config.assetbrowser_dir`
5. **Exports items to Google Sheets** (optional, requires credentials)

**Requirements:**
- 7-Zip must be in PATH
- Google Sheets credentials in `gsheet_credentials.json` (optional)

### Main.py Integration with Versioning

When `main.py` is run with `--version` parameter:
1. Loads assets **once** (performance optimization)
2. Generates asset browser HTML files
3. Creates version snapshot (reuses loaded assets)
4. Generates HTML version report comparing to previous version
5. All outputs go to `config.assetbrowser_dir`

**Key Implementation Detail:**
- `create_snapshot()` accepts optional `assets` parameter to avoid double-loading
- Version report is automatically generated if 2+ versions exist in database
- Use `--prev-version` to override default comparison (latest - 1)

## Important Implementation Notes

### RDA Extraction
- **RDAConsole Integration**: Uses RDAConsole.exe for extracting game files
- **Subprocess Issues**: RDAConsole requires `shell=True` and `CREATE_NEW_CONSOLE` to avoid console handle errors
- **Extraction Strategy**:
  - All files from `config.rda`
  - Icon files from `ui.rda` (filter: `.*icon.*`)
  - `.ifo` files from `graphics_*.rda` (filter: `.*\.ifo$`)

### Attribute Parsing Critical Points
- **ReferenceAttribute Recursion**: NEVER iterate ReferenceAttribute in recursive functions to avoid infinite loops
- **FileNameAttribute Path Resolution**: Complex logic for resolving DDS/image paths with fallbacks to alternative subfolders
- **Boolean Parsing**: Custom `parse_bool()` function handles Anno's boolean representations
- **FloatOrPercental**: Special handling for attributes that can be either float values or percentages

### Asset Iteration Patterns
- **Safe Iteration**: Always use `list(assets)` and `list(assets.templates)` like in `convert.py`
- **Asset Cache**: AssetCache provides unified access to both assets and templates
- **Print Tree**: Use `asset.print_tree()` to see complete resolved inheritance chain

## Testing and Analysis
- The project uses **pytest** for integration testing
- Test suite location: `tests/integration/`
- Shared fixtures: `tests/conftest.py` (provides `assets`, `config`, `ui_text_cache`, `texts`)
- Run tests with: `test.cmd` or `uv run nox -s test` or `uv run pytest`
- See `tests/README.md` for comprehensive testing guide
- When creating scripts to track the program behaviour, always put them into `tests/debugging`
- When creating scripts to test the correct output, always put them into `tests/integration`. The script should become a permanent test case after the feature was implemented.
- New tests should follow pytest conventions and use the shared fixtures from `conftest.py`


## VS Code Integration

Launch configurations are provided in `.vscode/launch.json`:
- "Python Debugger: Main": Run main.py
- "Run converter: Asset Browser": Run asset browser converter

## Dependencies

- **Core**: lxml, Jinja2, Wand
- **Development**: nox, pyright, ruff, uv
- **Optional**: Jupyter notebooks, code analysis tools

@AGENTS.md
