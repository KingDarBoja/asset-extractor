"""
Export functionality for asset versioning system.

This module provides functionality to export version data:
- Export all versions to CSV with hash columns per version
- Export single version to JSON with asset details
- Filter by template or changes only
"""

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from assetextractor.versioning.database import AssetVersionData, Version, VersionDatabase


@dataclass
class AssetExportData:
    """Asset data for all-versions export."""

    name: str | None
    template: str | None
    version_added: int
    version_deleted: int | None
    hashes: dict[int, str] = field(default_factory=dict)


@dataclass
class AssetJsonExport:
    """Asset data for single version JSON export."""

    guid: int
    name: str | None
    template: str | None
    hash: str
    version_added: str


@dataclass
class VersionJsonExport:
    """Version metadata for JSON export."""

    id: int
    version_string: str
    created_at: str
    description: str | None
    asset_count: int


@dataclass
class AssetHistoryEntry:
    """Asset version history entry."""

    version: str
    hash: str


@dataclass
class AssetAllVersionsExport:
    """Asset data with full version history for JSON export."""

    name: str | None
    template: str | None
    version_added: str
    version_deleted: str | None
    history: list[AssetHistoryEntry] = field(default_factory=list)


def export_versions(
    db: VersionDatabase,
    output_path: Path,
    output_format: str = "csv",
    version: str | None = None,
    changes_only: bool = False,
    template_filter: str | None = None,
) -> None:
    """
    Export version data to file.

    Args:
        db: Database instance
        output_path: Output file path
        output_format: Output format ("csv" or "json")
        version: Optional version to export (all if None)
        changes_only: If True, only export assets with changes
        template_filter: Optional template name filter

    Raises:
        ValueError: If version not found or invalid format
    """
    if output_format == "csv":
        export_csv(db, output_path, version, changes_only, template_filter)
    elif output_format == "json":
        export_json(db, output_path, version, template_filter)
    else:
        raise ValueError(f"Invalid output format: {output_format}")


def export_csv(
    db: VersionDatabase, output_path: Path, version: str | None, changes_only: bool, template_filter: str | None
) -> None:
    """
    Export versions to CSV.

    CSV Format (all versions):
    - Columns: guid, name, template, version_added, version_deleted, v1.0.0_hash, v1.0.1_hash, ...
    - One row per asset, columns for each version's hash

    CSV Format (single version):
    - Columns: guid, name, template, hash
    - One row per asset in that version

    Args:
        db: Database instance
        output_path: Output file path
        version: Optional version to export (all if None)
        changes_only: If True, only export assets with changes
        template_filter: Optional template name filter
    """
    if version:
        # Export single version
        version_obj = db.get_version_by_string(version)
        if version_obj is None:
            raise ValueError(f"Version '{version}' not found")

        export_single_version_csv(db, output_path, version_obj, template_filter)
    else:
        # Export all versions
        export_all_versions_csv(db, output_path, changes_only, template_filter)


def export_single_version_csv(
    db: VersionDatabase, output_path: Path, version_obj: Version, template_filter: str | None
) -> None:
    """Export a single version to CSV."""
    asset_versions: dict[int, AssetVersionData] = db.get_asset_versions(version_obj.id, template_filter)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["guid", "name", "template", "hash"])

        for guid, data in sorted(asset_versions.items()):
            writer.writerow([guid, data["name"] or "", data["template"] or "", data["hash"]])

    print(f"Exported {len(asset_versions)} assets from version '{version_obj.version_string}' to {output_path}")


def export_all_versions_csv(
    db: VersionDatabase, output_path: Path, changes_only: bool, template_filter: str | None
) -> None:
    """Export all versions to CSV with hash columns per version."""
    # Get all versions
    versions = db.get_all_versions()

    if not versions:
        raise ValueError("No versions found in database")

    # Build asset data structure
    asset_data: dict[int, AssetExportData] = {}

    for version in versions:
        asset_versions: dict[int, AssetVersionData] = db.get_asset_versions(version.id, template_filter)

        for guid, data in asset_versions.items():
            if guid not in asset_data:
                # Get asset lifecycle info
                asset = db.get_asset(guid)
                asset_data[guid] = AssetExportData(
                    name=data["name"],
                    template=data["template"],
                    version_added=asset.version_added if asset else version.id,
                    version_deleted=asset.version_deleted if asset else None,
                )

            asset_data[guid].hashes[version.id] = data["hash"]

    # Filter for changes only
    if changes_only:
        filtered_data: dict[int, AssetExportData] = {}
        for guid, data in asset_data.items():
            # Asset has changes if it has different hashes across versions
            hashes = list(data.hashes.values())
            if len(set(hashes)) > 1:  # More than one unique hash
                filtered_data[guid] = data
        asset_data = filtered_data

    # Write CSV
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header: guid, name, template, version_added, version_deleted, v1_hash, v2_hash, ...
        header = ["guid", "name", "template", "version_added", "version_deleted"]
        header.extend([f"{v.version_string}_hash" for v in versions])
        writer.writerow(header)

        # Data rows
        for guid in sorted(asset_data.keys()):
            data = asset_data[guid]
            row = [guid, data.name or "", data.template or "", data.version_added, data.version_deleted or ""]

            # Add hash for each version (empty if asset not in that version)
            for version in versions:
                row.append(data.hashes.get(version.id, ""))

            writer.writerow(row)

    print(f"Exported {len(asset_data)} assets across {len(versions)} versions to {output_path}")


def export_json(db: VersionDatabase, output_path: Path, version: str | None, template_filter: str | None) -> None:
    """
    Export versions to JSON.

    JSON Format (single version):
    {
        "version": str,
        "created_at": str,
        "description": str,
        "asset_count": int,
        "assets": [
            {"guid": int, "name": str, "template": str, "hash": str, "version_added": str},
            ...
        ]
    }

    JSON Format (all versions):
    {
        "versions": [
            {"version_string": str, "created_at": str, "asset_count": int, ...},
            ...
        ],
        "assets": {
            "guid": {
                "name": str,
                "template": str,
                "version_added": str,
                "version_deleted": str,
                "history": [
                    {"version": str, "hash": str},
                    ...
                ]
            },
            ...
        }
    }

    Args:
        db: Database instance
        output_path: Output file path
        version: Optional version to export (all if None)
        template_filter: Optional template name filter
    """
    if version:
        # Export single version
        version_obj = db.get_version_by_string(version)
        if version_obj is None:
            raise ValueError(f"Version '{version}' not found")

        export_single_version_json(db, output_path, version_obj, template_filter)
    else:
        # Export all versions
        export_all_versions_json(db, output_path, template_filter)


def export_single_version_json(
    db: VersionDatabase, output_path: Path, version_obj: Version, template_filter: str | None
) -> None:
    """Export a single version to JSON."""
    asset_versions: dict[int, AssetVersionData] = db.get_asset_versions(version_obj.id, template_filter)

    # Build asset list
    assets_list: list[AssetJsonExport] = []
    for guid in sorted(asset_versions.keys()):
        data = asset_versions[guid]
        asset_obj = db.get_asset(guid)

        # Get version_added as version string
        version_added_str = ""
        if asset_obj:
            version_added = db.get_version_by_id(asset_obj.version_added)
            version_added_str = version_added.version_string if version_added else ""

        assets_list.append(
            AssetJsonExport(
                guid=guid,
                name=data["name"],
                template=data["template"],
                hash=data["hash"],
                version_added=version_added_str,
            )
        )

    result = {
        "version": version_obj.version_string,
        "created_at": version_obj.created_at,
        "description": version_obj.description,
        "asset_count": version_obj.asset_count,
        "assets": [asdict(a) for a in assets_list],
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Exported {len(assets_list)} assets from version '{version_obj.version_string}' to {output_path}")


def export_all_versions_json(db: VersionDatabase, output_path: Path, template_filter: str | None) -> None:
    """Export all versions to JSON."""
    versions = db.get_all_versions()

    if not versions:
        raise ValueError("No versions found in database")

    # Build version list
    versions_list = [
        VersionJsonExport(
            id=v.id,
            version_string=v.version_string,
            created_at=v.created_at,
            description=v.description,
            asset_count=v.asset_count,
        )
        for v in versions
    ]

    # Build version string map
    version_id_to_string = {v.id: v.version_string for v in versions}

    # Build asset data
    assets_dict: dict[int, AssetAllVersionsExport] = {}

    for version in versions:
        asset_versions: dict[int, AssetVersionData] = db.get_asset_versions(version.id, template_filter)

        for guid, data in asset_versions.items():
            if guid not in assets_dict:
                # Get asset lifecycle info
                asset = db.get_asset(guid)
                version_added_str = version_id_to_string.get(asset.version_added, "") if asset else ""
                version_deleted_str = (
                    version_id_to_string.get(asset.version_deleted, "") if asset and asset.version_deleted else None
                )

                assets_dict[guid] = AssetAllVersionsExport(
                    name=data["name"],
                    template=data["template"],
                    version_added=version_added_str,
                    version_deleted=version_deleted_str,
                )

            # Add to history
            assets_dict[guid].history.append(AssetHistoryEntry(version=version.version_string, hash=data["hash"]))

    result = {
        "versions": [asdict(v) for v in versions_list],
        "assets": {guid: asdict(asset) for guid, asset in assets_dict.items()},
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Exported {len(assets_dict)} assets across {len(versions)} versions to {output_path}")
