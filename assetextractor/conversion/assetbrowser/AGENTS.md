# Asset Browser Implementation Guide

## Summary

The asset browser generates static HTML pages from Anno 117 asset data using Jinja2 templates. Each page features pure CSS tabs (Composed/References/XML), enhanced tooltips showing source locations and metadata, and reusable table macros for consistent formatting. The converter enforces XML indentation and creates a browsable reference of all assets and templates.

## Overview

The asset browser generates static HTML pages from Anno 117 asset data, with:
- **Tabbed layout**: Composed view, References, and XML
- **Enhanced tooltips**: Show source information, meta definitions, and template references
- **Common table rendering**: Reusable macros for consistent presentation

## Architecture

```
assetbrowser/
├── convert.py                 # Main converter class
├── styles.css                 # CSS with pure CSS tabs
└── templates/
    ├── macros.html           # Shared macros (tooltips & tables)
    ├── asset.html            # Individual asset pages
    ├── template.html         # Template definition pages
    └── template_cache.html   # Index/overview page
```

## Core Components

### 1. Converter (convert.py)

**Key responsibilities**:
- Loads AssetCache from config
- Renders templates using Jinja2
- Generates HTML files to `C:\temp\assetbrowser-2025-12-08\`
- Enforces XML indentation using lxml's `indent()` function

**XML formatting**:
```python
# Create deep copy to avoid modifying original
node_copy = deepcopy(element.node)
# Force 2-space indentation regardless of source
indent(node_copy, space="  ")
# Convert to string
xml = escape(tostring(node_copy, encoding="unicode"))
```

**Why deep copy?** Source XML has no indentation, so we must force it without modifying the original asset nodes.

### 2. Shared Macros (templates/macros.html)

#### enhanced_tooltip(node)

Generates multi-line tooltip text for any NamedElement (Asset, Template, Attribute, Property).

**Displays**:
- Data type (from `node.meta.data_type`)
- Optional flag, min/max ranges, dataset name
- Property description
- **Meta source**: `node.meta.source` (where property definition comes from, e.g., "properties-meta:567")
- **Template name**: For TemplateAttribute instances (e.g., "Template: BuildingBuff")
- **Attribute source**: `node.source` (where value comes from in XML, e.g., "assets-117.xml:1234" or "DEFAULT")

**Usage**:
```jinja2
<a href="..." title="{{ enhanced_tooltip(node) }}">Link</a>
```

#### render_reference_table(key, ref_dict, is_asset_view=true)

Renders reference tables with three columns:
- **Template**: Link to template with tooltip
- **Asset/GUID**: Link to asset (or GUID for template view) with tooltip
- **Path/Probability**: Property path or probability percentage for reward pools

**Parameters**:
- `is_asset_view=true`: Shows who references this asset (asset pages)
- `is_asset_view=false`: Shows instances of this template (template pages)

### 3. Page Templates

#### asset.html

**Structure**:
```jinja2
{% from 'macros.html' import enhanced_tooltip, render_reference_table %}

<div class="tabs">
  <input type="radio" id="tab-pretty" checked>
  <label for="tab-pretty">Composed</label>
  <!-- More tabs -->

  <div class="tab-panels">
    <div class="tab-panel" id="panel-pretty">
      <!-- Tree view with render_node macro -->
    </div>
    <div class="tab-panel" id="panel-refs">
      {% for key, ref_dict in asset.named_reference_collections.items() %}
        {{ render_reference_table(key, ref_dict, is_asset_view=true) }}
      {% endfor %}
    </div>
    <div class="tab-panel" id="panel-xml">
      <pre class="xml-display">{{ xml }}</pre>
    </div>
  </div>
</div>
```

**render_node(node)** macro:
- Recursive macro defined inline
- Handles ReferenceAttribute, compound attributes, primitive attributes
- Applies tooltips to all spans and links
- Marks inherited/default values with CSS classes

#### template.html

Same structure as asset.html but with `is_asset_view=false` for reference tables.

### 4. Styling (styles.css)

**Pure CSS tabs** (no JavaScript):
```css
.tabs input[type="radio"] { display: none; }
.tabs input:checked + label { background-color: white; font-weight: bold; }
.tab-panel { display: none; }
#tab-pretty:checked ~ .tab-panels #panel-pretty { display: block; }
```

**How it works**: Radio buttons are hidden, clicking labels toggles which panel is visible via CSS sibling selectors.

**XML display**:
```css
.xml-display {
  font-family: 'Courier New', monospace;
  white-space: pre;  /* Preserves indentation */
  background-color: #f5f5f5;
}
```

## Key Design Decisions

### 1. Why Pure CSS Tabs?
- No JavaScript dependencies → works in static HTML
- Faster page load and rendering
- Simple implementation using radio button technique

### 2. Why Separate Macros File?
- DRY principle: single source of truth for tooltips
- Easy to maintain and extend
- Reusable across asset.html and template.html

### 3. Why Deep Copy for XML?
- Source XML from game has no indentation
- Must force indentation without modifying original asset nodes
- lxml's `indent()` modifies in-place, so we copy first

### 4. Why Multi-line Tooltips?
- Native browser tooltips support `\n` for line breaks
- No custom popover needed (simpler implementation)
- Shows comprehensive info: meta source + attribute source + template

## Common Modifications

### Adding New Tooltip Information
Edit `enhanced_tooltip()` macro in `macros.html`:
```jinja2
{# Add new info #}
{%- if node.your_new_property is defined -%}
    {%- set text = text + "\nYour Label: " + node.your_new_property|string -%}
{%- endif -%}
```

### Adding New Tab
1. Add radio input and label in template
2. Add `.tab-panel` div with content
3. Add CSS selector to show panel when radio is checked

### Changing Table Columns
Edit `render_reference_table()` macro in `macros.html` to modify `<th>` and `<td>` elements.

### Changing XML Indentation
Modify `indent(node_copy, space="  ")` in convert.py (default is 2 spaces).

## Testing

Run converter:
```bash
uv run python -m assetextractor.conversion.assetbrowser.convert
```

Output location: `C:\temp\assetbrowser-2025-12-08\`

Check:
1. Tooltips show all source information (hover over any attribute)
2. Tabs switch correctly (click each tab label)
3. XML is properly indented with 2 spaces per level
4. Reference tables show Template, Asset/GUID, and Path columns
5. Path column shows property paths (not "-" for all entries)

## Important Notes

- **Do not modify original nodes**: Always use `deepcopy()` before calling `indent()`
- **Tooltips use title attribute**: Multi-line via `\n` character
- **Tabs use unique IDs**: `tab-pretty`, `tab-refs`, `tab-xml` must match panel IDs
- **Macros must be imported**: Always `{% from 'macros.html' import ... %}` at top of templates
- **XML needs explicit indentation**: Source XML has none, must force it with `indent()`
