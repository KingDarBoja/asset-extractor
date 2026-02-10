"""
HTML report generation for asset versioning system.

This module provides functionality to generate HTML reports comparing
two versions, with filtering for Items and Pools, and links to the
asset browser.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.versioning.database import VersionDatabase
from assetextractor.versioning.diff import compare_versions


def generate_version_report(
    db_path: Path, version1_str: str, version2_str: str, output_dir: Path, config: Config | None = None
) -> Path:
    """
    Generate HTML report comparing two versions, grouped by template.

    Process:
        1. Open database, load versions
        2. Get diff for each template separately (Item, ItemWithBoost, Pool types)
        3. Load asset cache for nice names (optional)
        4. Render Jinja2 template with per-template sections
        5. Write to output_dir/version_report_{v1}_{v2}.html

    Args:
        db_path: Path to SQLite database
        version1_str: First version identifier (older)
        version2_str: Second version identifier (newer)
        output_dir: Output directory for HTML file
        config: Optional config for loading asset names

    Returns:
        Path to generated HTML file

    Raises:
        ValueError: If versions not found
        FileNotFoundError: If template not found
    """
    db = VersionDatabase(db_path)

    try:
        print(f"Comparing versions {version1_str} and {version2_str}...")

        # Get templates to report on
        templates_to_report = _get_templates_to_report(db, version1_str, version2_str)

        # Get diff for each template
        print(f"Getting diffs for {len(templates_to_report)} templates...")
        template_diffs = {}
        overall_summary = {"added_count": 0, "changed_count": 0, "deleted_count": 0}

        for template_name in templates_to_report:
            diff = compare_versions(db, version1_str, version2_str, template_filter=template_name)
            template_diffs[template_name] = diff

            # Accumulate totals
            overall_summary["added_count"] += diff["summary"]["added_count"]
            overall_summary["changed_count"] += diff["summary"]["changed_count"]
            overall_summary["deleted_count"] += diff["summary"]["deleted_count"]

        # Load asset names (optional)
        asset_names = {}
        if config:
            try:
                print("Loading asset names from cache...")
                assets = AssetCache.load(config)
                asset_names = {asset.guid: str(asset) for asset in assets.elements.values()}
                print(f"Loaded {len(asset_names):,} asset names")
            except Exception as e:
                print(f"Warning: Could not load asset names: {e}")

        # Render template
        print("Rendering HTML template...")
        template_dir = Path(__file__).parent.parent / "conversion" / "assetbrowser" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("version_report.html")

        html = template.render(
            version1=version1_str,
            version2=version2_str,
            template_diffs=template_diffs,
            overall_summary=overall_summary,
            asset_names=asset_names,
        )

        # Write output
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_v1 = version1_str.replace(".", "_").replace(" ", "_")
        safe_v2 = version2_str.replace(".", "_").replace(" ", "_")
        output_path = output_dir / f"version_report_{safe_v1}_{safe_v2}.html"
        output_path.write_text(html, encoding="utf-8")

        print(f"Report generated: {output_path}")
        return output_path

    finally:
        db.close()


def _get_templates_to_report(db: VersionDatabase, version1_str: str, version2_str: str) -> list[str]:
    """
    Get list of templates to include in report.

    Includes Item, ItemWithBoost, and all *Pool templates that have changes.

    Args:
        db: Database instance
        version1_str: First version identifier
        version2_str: Second version identifier

    Returns:
        Sorted list of template names
    """
    v1 = db.get_version_by_string(version1_str)
    v2 = db.get_version_by_string(version2_str)

    if v1 is None or v2 is None:
        return []

    # Ensure v1 is older
    if v1.id > v2.id:
        v1, v2 = v2, v1

    # Get all templates from both versions
    v1_assets = db.get_all_assets_in_version(v1.id)
    v2_assets = db.get_all_assets_in_version(v2.id)

    templates = set[str]()
    for asset_data in v1_assets.values():
        template = asset_data.get("template")
        if template and _should_include_template(template):
            templates.add(template)

    for asset_data in v2_assets.values():
        template = asset_data.get("template")
        if template and _should_include_template(template):
            templates.add(template)

    return sorted(templates)


def _should_include_template(template_name: str) -> bool:
    """Check if template should be included in report."""
    return True #template_name in ("Item", "ItemWithBoost", "CityStatus", ) or "Pool" in template_name
