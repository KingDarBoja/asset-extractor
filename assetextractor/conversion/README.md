# Asset Conversion Tools

This directory contains various converters that transform parsed Anno game data into different formats for analysis and use in external applications.

## Available Converters

### Statistics (`statistics/`)
**Purpose:** Simple extraction and saving of asset data.

**What you can learn:**
- Recursive attribute traversal techniques while avoiding infinite loops (ReferenceAttribute handling)

### Asset Browser (`assetbrowser/`)
**Purpose:** Generates interactive HTML pages for browsing game assets and templates.

**What you can learn:**
- How to iterate safely through assets using `list(assets)` and `list(assets.templates)` patterns
- Jinja2 template usage for rendering asset data into HTML with proper escaping
- Basic asset-to-HTML conversion workflow with CSS styling and file organization

### Calculator (`calculator/`)
**Purpose:** Extracts game data into JSON format for the Anno 117 production calculator web application.

**What you can learn:**
- Complex asset data extraction patterns for production chains, population needs, and building effects
- How to resolve asset relationships (producers, consumers, buff targets) across the entire game data
- JSON schema generation for type-safe data exchange with external applications
- Reading images and encoding them as base64
- Extracting texts with all localizations

## Usage Examples

Each converter can be run independently:
- **Asset Browser**: `uv run assetextractor/conversion/assetbrowser/convert.py`
- **Calculator**: Open and run `calculator/conversion_calculator.ipynb`
- **Statistics**: Open and run notebooks in `statistics/` directory

See individual converter directories for specific usage instructions and examples.