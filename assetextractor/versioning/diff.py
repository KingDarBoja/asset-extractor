"""
Version comparison logic for asset versioning system.

This module provides functionality to compare two versions and:
- Identify added assets (in v2 but not v1)
- Identify deleted assets (in v1 but not v2)
- Identify changed assets (in both but with different hash)
- Format output as text, JSON, or CSV
"""

import csv
import json
from pathlib import Path
from typing import TypedDict

from assetextractor.versioning.database import VersionDatabase


class AssetChangeData(TypedDict):
    """Asset data for added/deleted assets."""

    guid: int
    name: str | None
    template: str | None
    hash: str


class AssetModifiedData(TypedDict):
    """Asset data for changed assets."""

    guid: int
    name: str | None
    template: str | None
    old_hash: str
    new_hash: str


class AssetUnchangedData(TypedDict):
    """Asset data for unchanged assets."""

    guid: int
    name: str | None
    template: str | None
    hash: str


class DiffSummary(TypedDict):
    """Summary statistics for version diff."""

    added_count: int
    deleted_count: int
    changed_count: int
    unchanged_count: int


class VersionDiff(TypedDict):
    """Complete version diff result."""

    version1: str
    version2: str
    added: list[AssetChangeData]
    deleted: list[AssetChangeData]
    changed: list[AssetModifiedData]
    unchanged: list[AssetUnchangedData]
    summary: DiffSummary


def compare_versions(
    db: VersionDatabase, version1_str: str, version2_str: str, template_filter: str | None = None
) -> VersionDiff:
    """
    Compare two versions and return changes.

    Args:
        db: Database instance
        version1_str: First version identifier (older)
        version2_str: Second version identifier (newer)
        template_filter: Optional template name filter

    Returns:
        Dict with comparison results:
        {
            "version1": str,
            "version2": str,
            "added": list[dict],
            "deleted": list[dict],
            "changed": list[dict],
            "unchanged": list[dict],
            "summary": {
                "added_count": int,
                "deleted_count": int,
                "changed_count": int,
                "unchanged_count": int
            }
        }

    Raises:
        ValueError: If version not found or versions are the same
    """
    # Get version records
    v1 = db.get_version_by_string(version1_str)
    v2 = db.get_version_by_string(version2_str)

    if v1 is None:
        raise ValueError(f"Version '{version1_str}' not found")
    if v2 is None:
        raise ValueError(f"Version '{version2_str}' not found")

    if v1.id == v2.id:
        raise ValueError("Cannot compare a version with itself")

    # Ensure v1 is older than v2 (swap if needed)
    if v1.id > v2.id:
        v1, v2 = v2, v1
        version1_str, version2_str = version2_str, version1_str

    # Get all assets for both versions (including unchanged)
    v1_assets = db.get_all_assets_in_version(v1.id, template_filter)
    v2_assets = db.get_all_assets_in_version(v2.id, template_filter)

    v1_guids = set(v1_assets.keys())
    v2_guids = set(v2_assets.keys())

    # Categorize changes
    added: list[AssetChangeData] = []
    deleted: list[AssetChangeData] = []
    changed: list[AssetModifiedData] = []
    unchanged: list[AssetUnchangedData] = []

    # Added assets (in v2 but not v1)
    for guid in v2_guids - v1_guids:
        added.append(
            {
                "guid": guid,
                "name": v2_assets[guid]["name"],
                "template": v2_assets[guid]["template"],
                "hash": v2_assets[guid]["hash"],
            }
        )

    # Deleted assets (in v1 but not v2)
    for guid in v1_guids - v2_guids:
        deleted.append(
            {
                "guid": guid,
                "name": v1_assets[guid]["name"],
                "template": v1_assets[guid]["template"],
                "hash": v1_assets[guid]["hash"],
            }
        )

    # Changed or unchanged assets (in both)
    for guid in v1_guids & v2_guids:
        v1_hash = v1_assets[guid]["hash"]
        v2_hash = v2_assets[guid]["hash"]

        if v1_hash != v2_hash:
            changed.append(
                {
                    "guid": guid,
                    "name": v2_assets[guid]["name"],
                    "template": v2_assets[guid]["template"],
                    "old_hash": v1_hash,
                    "new_hash": v2_hash,
                }
            )
        else:
            unchanged.append(
                {
                    "guid": guid,
                    "name": v2_assets[guid]["name"],
                    "template": v2_assets[guid]["template"],
                    "hash": v1_hash,
                }
            )

    # Sort by GUID for consistent output
    added.sort(key=lambda x: x["guid"])
    deleted.sort(key=lambda x: x["guid"])
    changed.sort(key=lambda x: x["guid"])

    return {
        "version1": version1_str,
        "version2": version2_str,
        "added": added,
        "deleted": deleted,
        "changed": changed,
        "unchanged": unchanged,
        "summary": {
            "added_count": len(added),
            "deleted_count": len(deleted),
            "changed_count": len(changed),
            "unchanged_count": len(unchanged),
        },
    }


def format_diff_text(diff: VersionDiff, verbose: bool = False) -> str:
    """
    Format diff as human-readable text.

    Args:
        diff: Diff result from compare_versions()
        verbose: If True, show hashes and all details

    Returns:
        Formatted text string
    """
    lines: list[str] = []

    # Header
    lines.append(f"Comparing versions: {diff['version1']} -> {diff['version2']}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    summary = diff["summary"]
    lines.append("Summary:")
    lines.append(f"  Added:     {summary['added_count']:,} assets")
    lines.append(f"  Changed:   {summary['changed_count']:,} assets")
    lines.append(f"  Deleted:   {summary['deleted_count']:,} assets")
    lines.append(f"  Unchanged: {summary['unchanged_count']:,} assets")
    lines.append("")

    # Added assets
    if diff["added"]:
        lines.append(f"Added Assets ({summary['added_count']}):")
        for asset in diff["added"]:
            name = asset["name"] or f"GUID {asset['guid']}"
            template = asset["template"] or "Unknown"
            lines.append(f"  [{asset['guid']}] {name} (Template: {template})")
            if verbose:
                lines.append(f"    Hash: {asset['hash']}")
        lines.append("")

    # Changed assets
    if diff["changed"]:
        lines.append(f"Changed Assets ({summary['changed_count']}):")
        for asset in diff["changed"]:
            name = asset["name"] or f"GUID {asset['guid']}"
            template = asset["template"] or "Unknown"
            lines.append(f"  [{asset['guid']}] {name} (Template: {template})")
            if verbose:
                lines.append(f"    Old hash: {asset['old_hash']}")
                lines.append(f"    New hash: {asset['new_hash']}")
        lines.append("")

    # Deleted assets
    if diff["deleted"]:
        lines.append(f"Deleted Assets ({summary['deleted_count']}):")
        for asset in diff["deleted"]:
            name = asset["name"] or f"GUID {asset['guid']}"
            template = asset["template"] or "Unknown"
            lines.append(f"  [{asset['guid']}] {name} (Template: {template})")
            if verbose:
                lines.append(f"    Hash: {asset['hash']}")
        lines.append("")

    return "\n".join(lines)


def format_diff_json(diff: VersionDiff) -> str:
    """
    Format diff as JSON.

    Args:
        diff: Diff result from compare_versions()

    Returns:
        JSON string
    """
    return json.dumps(diff, indent=2)


def format_diff_csv(diff: VersionDiff, output_path: Path) -> None:
    """
    Format diff as CSV.

    Args:
        diff: Diff result from compare_versions()
        output_path: Path to write CSV file
    """
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(["change_type", "guid", "name", "template", "old_hash", "new_hash"])

        # Added assets
        for asset in diff["added"]:
            writer.writerow(["added", asset["guid"], asset["name"] or "", asset["template"] or "", "", asset["hash"]])

        # Changed assets
        for asset in diff["changed"]:
            writer.writerow(
                [
                    "changed",
                    asset["guid"],
                    asset["name"] or "",
                    asset["template"] or "",
                    asset["old_hash"],
                    asset["new_hash"],
                ]
            )

        # Deleted assets
        for asset in diff["deleted"]:
            writer.writerow(["deleted", asset["guid"], asset["name"] or "", asset["template"] or "", asset["hash"], ""])


def write_diff(
    diff: VersionDiff, output_format: str = "text", output_path: Path | None = None, verbose: bool = False
) -> None:
    """
    Write diff to file or stdout.

    Args:
        diff: Diff result from compare_versions()
        output_format: Output format ("text", "json", or "csv")
        output_path: Optional output file path (stdout if None)
        verbose: Show detailed information (text format only)
    """
    if output_format == "text":
        text = format_diff_text(diff, verbose)
        if output_path:
            output_path.write_text(text, encoding="utf-8")
            print(f"Diff written to {output_path}")
        else:
            print(text)

    elif output_format == "json":
        json_text = format_diff_json(diff)
        if output_path:
            output_path.write_text(json_text, encoding="utf-8")
            print(f"Diff written to {output_path}")
        else:
            print(json_text)

    elif output_format == "csv":
        if output_path is None:
            raise ValueError("CSV format requires --output parameter")
        format_diff_csv(diff, output_path)
        print(f"Diff written to {output_path}")

    else:
        raise ValueError(f"Invalid output format: {output_format}")
