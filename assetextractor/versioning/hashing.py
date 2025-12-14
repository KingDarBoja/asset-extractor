"""
Recursive hash calculation for asset versioning system.

This module provides functions to calculate asset hashes that include:
- The asset's own XML content
- Hashes of referenced buff assets (Effect.Buffs) recursively
- Hashes of referenced target assets (Effect.Targets) - for pools, includes GUIDs only
- Hashes of referenced pool assets (RewardPool/AssetPool) recursively

The recursive approach ensures that changes to buffs, targets, or nested pools
are reflected in the hashes of assets that reference them.
"""

import hashlib

import lxml.etree as et

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import ListAttribute


def get_asset_hash_recursive(
    asset: Asset, visited: set[int] | None = None, hash_cache: dict[int, str] | None = None
) -> str:
    """
    Calculate recursive hash including referenced buffs, targets, and pools.

    This function computes a SHA-256 hash that includes:
    1. The asset's own canonical XML
    2. Hashes of referenced buff assets (from Effect.Buffs)
    3. Hashes/GUIDs of referenced target assets (from Effect.Targets)
    4. Hashes of referenced pool assets (from RewardPool/AssetPool)

    The recursive approach ensures that:
    - Items with modified buffs show as changed
    - Items with modified targets show as changed
    - Pools with modified nested pools show as changed
    - Pool structure changes are tracked (not item content)

    Args:
        asset: Asset object with .node, .guid, .template, .find() attributes
        visited: Set of asset GUIDs already visited (cycle detection)
        hash_cache: Dict mapping GUID to hash (performance optimization)

    Returns:
        SHA-256 hash as hexadecimal string

    Note:
        - Pools only include hashes of nested POOLS, not items
        - Target pools include only GUIDs, not full asset hashes
        - Uses visited.copy() to allow different branches to visit same nodes
        - Hash cache should be cleared between snapshot runs
    """
    # Initialize cycle detection
    if visited is None:
        visited = set()

    # Check for cycles
    if asset.guid in visited:
        return ""  # Return empty string for cycles

    # Check cache
    if hash_cache is not None and asset.guid in hash_cache:
        return hash_cache[asset.guid]

    # Add to visited set
    visited.add(asset.guid)

    # Collect hash components
    hash_components: list[bytes] = []

    # 1. Hash own XML (canonical form)
    try:
        xml_bytes = et.tostring(asset.node, method="c14n")
        hash_components.append(xml_bytes)
    except Exception:
        # If XML conversion fails, use empty bytes
        hash_components.append(b"")

    # 2. Collect buff hashes (Effect.Buffs)
    buff_hashes = _collect_buff_hashes(asset, visited, hash_cache)
    hash_components.extend(buff_hashes)

    # 3. Collect target hashes (Effect.Targets)
    target_hashes = _collect_target_hashes(asset, visited, hash_cache)
    hash_components.extend(target_hashes)

    # 4. Collect pool hashes (RewardPool/AssetPool)
    pool_hashes = _collect_pool_hashes(asset, visited, hash_cache)
    hash_components.extend(pool_hashes)

    # 5. Sort components for deterministic ordering
    # Keep own XML first, sort the rest
    own_xml = hash_components[0]
    other_components = sorted(hash_components[1:])
    sorted_components = [own_xml, *other_components]

    # 6. Combine and hash
    combined = b"".join(sorted_components)
    final_hash = hashlib.sha256(combined).hexdigest()

    # 7. Cache result
    if hash_cache is not None:
        hash_cache[asset.guid] = final_hash

    return final_hash


def _collect_buff_hashes(asset: Asset, visited: set[int], hash_cache: dict[int, str] | None) -> list[bytes]:
    """
    Collect hashes of referenced buff assets from Effect.Buffs.

    Args:
        asset: Asset object
        visited: Set of visited GUIDs
        hash_cache: Hash cache dict

    Returns:
        List of hash bytes to include in parent hash
    """
    hashes: list[bytes] = []

    try:
        # Try to get Effect.Buffs list
        buff_list = asset.find("Effect.Buffs")

        if buff_list and isinstance(buff_list, ListAttribute):
            for buff_entry in buff_list:
                try:
                    # Get the GUID attribute
                    buff_ref = buff_entry.find_ref("GUID")

                    # Check if it's a valid Asset
                    if buff_ref:
                        # Recursively hash the buff asset
                        buff_hash = get_asset_hash_recursive(buff_ref, visited.copy(), hash_cache)

                        if buff_hash:
                            hashes.append(buff_hash.encode())
                except (AttributeError, Exception):
                    # Skip this buff entry if it causes errors
                    continue

    except (AttributeError, Exception):
        # Asset doesn't have Effect.Buffs or it's not accessible
        pass

    return hashes


def _collect_pool_hashes(asset: Asset, visited: set[int], hash_cache: dict[int, str] | None) -> list[bytes]:
    """
    Collect hashes of referenced pool assets (RewardPool/AssetPool).

    CRITICAL: Only includes POOL references, not item references.
    This ensures pools track structural changes, not item content changes.

    Args:
        asset: Asset object
        visited: Set of visited GUIDs
        hash_cache: Hash cache dict

    Returns:
        List of hash bytes to include in parent hash
    """
    hashes: list[bytes] = []

    # Check if this asset is a pool
    is_reward_pool = "RewardPool" in asset.template.name
    is_asset_pool = "AssetPool" in asset.template.name

    if not (is_reward_pool or is_asset_pool):
        return hashes  # Not a pool, nothing to collect

    try:
        entries = None

        # Get the appropriate entry list
        if is_reward_pool:
            entries = asset.find("RewardPool.ItemsPool")
        elif is_asset_pool:
            entries = asset.find("AssetPool.AssetList")

        # Process entries
        if entries and isinstance(entries, ListAttribute):
            for entry in entries:
                try:
                    ref = None

                    # Get the referenced asset
                    if is_reward_pool and hasattr(entry, "ItemLink"):
                        ref = entry.find_ref("ItemLink")
                    elif is_asset_pool and hasattr(entry, "Asset"):
                        ref = entry.find_ref("Asset")

                    # CRITICAL: Only include if reference is also a pool
                    if ref and hasattr(ref, "template") and "Pool" in ref.template.name:
                        # Recursively hash the pool
                        pool_hash = get_asset_hash_recursive(ref, visited.copy(), hash_cache)

                        if pool_hash:
                            hashes.append(pool_hash.encode())

                except (AttributeError, Exception):
                    # Skip this entry if it causes errors
                    continue

    except (AttributeError, Exception):
        # Pool doesn't have the expected structure
        pass

    return hashes


def _collect_target_hashes(asset: Asset, visited: set[int], hash_cache: dict[int, str] | None) -> list[bytes]:
    """
    Collect hashes of referenced target assets from Effect.Targets.

    If a target is a pool, includes all pool asset GUIDs (but not the assets themselves).
    Otherwise, recursively hashes the target asset.

    Args:
        asset: Asset object
        visited: Set of visited GUIDs
        hash_cache: Hash cache dict

    Returns:
        List of hash bytes to include in parent hash
    """
    hashes: list[bytes] = []

    try:
        # Try to get Effect.Targets list
        targets_list = asset.find("Effect.Targets")

        if targets_list and isinstance(targets_list, ListAttribute):
            for target_entry in targets_list:
                try:
                    # Get the GUID attribute
                    target_ref = target_entry.find_ref("GUID")

                    # Check if it's a valid Asset
                    if isinstance(target_ref, Asset):
                        guids = sorted([asset.guid for asset in target_ref.pool_assets()])
                        
                        for guid in guids:
                            hashes.append(str(guid).encode())
                except (AttributeError, Exception):
                    # Skip this target entry if it causes errors
                    continue

    except (AttributeError, Exception):
        # Asset doesn't have Effect.Targets or it's not accessible
        pass

    return hashes
