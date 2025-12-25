"""
Snapshot creation logic for asset versioning system.

This module provides functionality to create version snapshots by:
- Loading all assets from the cache
- Calculating SHA-256 hash of canonical XML for each asset
- Recording version metadata and asset states in the database
- Detecting added/changed/deleted assets compared to previous version
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

import lxml.etree as et

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.versioning.database import VersionDatabase
from assetextractor.versioning.hashing import get_asset_hash_recursive


class AssetData(TypedDict):
    """Asset data structure for snapshot processing."""

    guid: int
    name: str
    template_name: str | None
    xml_hash: str


class SnapshotStatistics(TypedDict):
    """Statistics returned by create_snapshot."""

    version_id: int
    version_string: str
    asset_count: int
    added: int
    changed: int
    deleted: int
    duration_seconds: float


def create_snapshot(
    config: Config,
    version_string: str,
    db_path: Path,
    description: str | None = None,
    force: bool = False,
    assets: AssetCache | None = None,
) -> SnapshotStatistics:
    """
    Create a new version snapshot.

    This function:
    1. Loads all assets from the cache (or uses provided assets)
    2. Checks if version already exists (error if duplicate and not force)
    3. Calculates SHA-256 hash for each asset using canonical XML
    4. Creates version record in database
    5. Tracks asset lifecycle (added/changed/deleted)
    6. Returns statistics

    Args:
        config: Configuration with game_path and cache_path
        version_string: Version identifier (e.g., "1.0.0", "Season 2")
        db_path: Path to SQLite database
        description: Optional version description
        force: If True, overwrite existing version
        assets: Optional pre-loaded AssetCache (for performance)

    Returns:
        Dict with statistics:
        {
            "version_id": int,
            "version_string": str,
            "asset_count": int,
            "added": int,
            "changed": int,
            "deleted": int,
            "duration_seconds": float
        }

    Raises:
        ValueError: If version already exists and force=False
        FileNotFoundError: If config or cache not found
    """
    start_time = datetime.now(timezone.utc)

    # Validate config
    if not config.cache_path.exists():
        raise FileNotFoundError(
            f"Cache directory not found at {config.cache_path}. "
            "Please run extraction first (extract.cmd or python -m assetextractor.extraction.extract)"
        )

    # Load assets if not provided
    if assets is None:
        print(f"Loading assets from {config.cache_path}...")
        assets = AssetCache.load(config)
        print(f"Loaded {len(assets.elements)} assets")
    else:
        print(f"Using pre-loaded assets ({len(assets.elements)} assets)")

    # Open database
    db = VersionDatabase(db_path)

    try:
        # Check if version exists
        existing_version = db.get_version_by_string(version_string)

        if existing_version and not force:
            raise ValueError(f"Version '{version_string}' already exists. Use --force to overwrite.")

        if force and existing_version:
            print(f"Deleting existing version '{version_string}'...")
            db.delete_version(existing_version.id)

        # Calculate hashes for all assets (recursive: includes buffs and pools)
        print("Calculating recursive asset hashes (includes buffs and pools)...")
        hash_cache: dict[int, str] = {}  # Cache for performance
        asset_data: list[AssetData] = []

        for i, asset in enumerate(assets.elements.values(), 1):
            if i % 1000 == 0:
                print(f"  Processed {i}/{len(assets.elements)} assets...")

            # Calculate recursive hash (includes Effect.Buffs and pool references)
            xml_hash = get_asset_hash_recursive(asset, hash_cache=hash_cache)

            asset_data.append(
                {
                    "guid": asset.guid,
                    "name": str(asset),
                    "template_name": asset.template.name if asset.template else None,
                    "xml_hash": xml_hash,
                }
            )

        print(f"Calculated hashes for {len(asset_data)} assets")

        # Create version snapshot in database
        print(f"Creating version snapshot '{version_string}'...")

        with db.transaction():
            # Create version record
            created_at = datetime.now(timezone.utc).isoformat()
            version_id = db.create_version(
                version_string=version_string,
                created_at=created_at,
                description=description,
                asset_count=len(asset_data),
            )

            # Get previous version (if exists)
            previous_version = db.get_latest_version_before(version_id)
            previous_guids = set[int]()
            previous_hashes: dict[int, str] = {}

            if previous_version:
                previous_guids = db.get_asset_guids_in_version(previous_version.id)
                # Build previous hash lookup for conditional inserts
                prev_asset_versions = db.get_asset_versions(previous_version.id)
                for guid, data in prev_asset_versions.items():
                    previous_hashes[guid] = data["hash"]
                print(f"  Loaded {len(previous_hashes):,} hashes from previous version")

            # Process each asset
            current_guids = set[int]()
            inserted_count = 0
            skipped_count = 0

            for i, data in enumerate(asset_data, 1):
                if i % 1000 == 0:
                    print(f"  Processing {i}/{len(asset_data)} assets...")

                guid = data["guid"]
                current_guids.add(guid)

                # Check if asset exists in assets table
                existing_asset = db.get_asset(guid)

                if existing_asset is None:
                    # New asset - insert into assets table
                    db.insert_asset(
                        guid=guid, name=data["name"], template_name=data["template_name"], version_added=version_id
                    )
                else:
                    # Existing asset - check if it was deleted and now re-added
                    if existing_asset.version_deleted is not None:
                        # Asset was deleted, now re-added
                        db.update_asset(guid, version_deleted=None)

                # CONDITIONAL INSERT: Only insert if hash changed or asset is new
                prev_hash = previous_hashes.get(guid)

                if prev_hash is None or prev_hash != data["xml_hash"]:
                    # Hash changed or new asset - insert asset_versions record
                    db.insert_asset_version(
                        guid=guid,
                        version_id=version_id,
                        xml_hash=data["xml_hash"],
                        name=data["name"],
                        template_name=data["template_name"],
                    )
                    inserted_count += 1
                else:
                    # Hash unchanged - skip insert
                    skipped_count += 1

            # Mark deleted assets (if there's a previous version)
            if previous_version:
                deleted_guids = previous_guids - current_guids

                for guid in deleted_guids:
                    db.update_asset(guid, version_deleted=version_id)

                if deleted_guids:
                    print(f"  Marked {len(deleted_guids)} assets as deleted")

            # Report insert statistics
            print(f"  Inserted {inserted_count:,} asset_versions rows (changed/new)")
            print(f"  Skipped {skipped_count:,} unchanged assets")

        print("Version snapshot created successfully")

        # Get statistics
        base_stats = db.get_version_statistics(version_id)

        # Add duration
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Construct final statistics with duration
        stats: SnapshotStatistics = {
            "version_id": base_stats["version_id"],
            "version_string": base_stats["version_string"],
            "asset_count": base_stats["asset_count"],
            "added": base_stats["added"],
            "changed": base_stats["changed"],
            "deleted": base_stats["deleted"],
            "duration_seconds": duration,
        }

        return stats

    finally:
        db.close()


def get_asset_hash(asset: Asset) -> str:
    """
    Calculate SHA-256 hash of asset's canonical XML.

    Args:
        asset: Asset object with .node attribute

    Returns:
        Hexadecimal hash string
    """
    xml_bytes = et.tostring(asset.node, method="c14n")
    return hashlib.sha256(xml_bytes).hexdigest()
