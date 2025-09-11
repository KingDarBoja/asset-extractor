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

### 3. Conversion (`assetextractor/conversion/`)
- **Purpose**: Generate excerpts in different formats (HTML, JSON)
- **Asset Browser** (`assetbrowser/`): HTML converter using Jinja2 templates
- **Status**: Partially implemented

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
# Run all checks (formatting, linting, type checking)
uv run nox

# Format code and fix issues
uv run nox -s format_fix

# Type checking only
uv run nox -s pyright

# Manual ruff commands
uv run ruff format .
uv run ruff check . --fix
```

### Running the Project
```bash
# Extract RDA files (run after game updates)
extract.cmd
# Or manually: uv run python -m assetextractor.extraction.extract

# Main entry point
uv run main

# Run asset browser converter directly
uv run assetextractor/conversion/assetbrowser/convert.py
```

## Configuration

- **config.json**: Contains `game_path` (Anno installation) and `cache_path` (extracted files location)
- **config.template.json**: Template for configuration setup

## Key Concepts

- **Asset Resolution**: The parser resolves all inheritance so `print_tree()` shows complete asset definitions
- **Meta Definitions**: Each attribute has metadata in `properties-toolone.xml` defining data types and constraints
- **Datasets**: Ordered collections of string literals (like enums) referenced by certain attributes
- **GUID System**: Assets are identified by unique GUIDs found in `Values/Standard/GUID`

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

The project includes several Jupyter notebooks for interactive development:
- `browsing.ipynb`: Main development interface
- `test_*.ipynb`: Various testing notebooks for specific functionality

## VS Code Integration

Launch configurations are provided in `.vscode/launch.json`:
- "Python Debugger: Main": Run main.py
- "Run converter: Asset Browser": Run asset browser converter

## Dependencies

- **Core**: lxml, Jinja2, Wand
- **Development**: nox, pyright, ruff, uv
- **Optional**: Jupyter notebooks, code analysis tools