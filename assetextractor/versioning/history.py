"""
Version history functionality for asset versioning system.

This module provides functionality to:
- Query version history
- Calculate statistics per version
- Format output as text or JSON
"""

import json
from dataclasses import asdict, dataclass

from assetextractor.versioning.database import VersionDatabase


@dataclass
class VersionInfo:
    """Version information structure."""

    version_string: str
    created_at: str
    description: str | None
    asset_count: int
    added: int = 0
    changed: int = 0
    deleted: int = 0


def get_version_history(db: VersionDatabase, verbose: bool = False) -> list[VersionInfo]:
    """
    Get version history with optional statistics.

    Args:
        db: Database instance
        verbose: If True, include change statistics for each version

    Returns:
        List of version dicts with metadata and optional statistics:
        [
            {
                "version_string": str,
                "created_at": str,
                "description": str,
                "asset_count": int,
                "added": int (if verbose),
                "changed": int (if verbose),
                "deleted": int (if verbose)
            },
            ...
        ]
    """
    versions = db.get_all_versions()

    history: list[VersionInfo] = []

    for version in versions:
        if verbose:
            stats = db.get_version_statistics(version.id)
            version_info = VersionInfo(
                version_string=version.version_string,
                created_at=version.created_at,
                description=version.description,
                asset_count=version.asset_count,
                added=stats["added"],
                changed=stats["changed"],
                deleted=stats["deleted"],
            )
        else:
            version_info = VersionInfo(
                version_string=version.version_string,
                created_at=version.created_at,
                description=version.description,
                asset_count=version.asset_count,
            )

        history.append(version_info)

    return history


def format_history_text(history: list[VersionInfo], verbose: bool = False) -> str:
    """
    Format version history as human-readable text.

    Args:
        history: History list from get_version_history()
        verbose: Show detailed statistics

    Returns:
        Formatted text string
    """
    if not history:
        return "No versions found in database."

    lines: list[str] = []
    lines.append("Version History")
    lines.append("=" * 60)
    lines.append("")

    # Reverse order to show newest first
    for version_info in reversed(history):
        lines.append(f"Version: {version_info.version_string}")
        lines.append(f"  Created: {version_info.created_at}")

        if version_info.description:
            lines.append(f"  Description: {version_info.description}")

        lines.append(f"  Total Assets: {version_info.asset_count:,}")

        if verbose:
            # Show changes (if not first version)
            if version_info.added == version_info.asset_count:
                lines.append("  Changes: Initial snapshot")
            else:
                changes: list[str] = []
                if version_info.added > 0:
                    changes.append(f"+{version_info.added} added")
                if version_info.changed > 0:
                    changes.append(f"{version_info.changed} changed")
                if version_info.deleted > 0:
                    changes.append(f"-{version_info.deleted} deleted")

                if changes:
                    lines.append(f"  Changes: {', '.join(changes)}")

        lines.append("")

    return "\n".join(lines)


def format_history_json(history: list[VersionInfo]) -> str:
    """
    Format version history as JSON.

    Args:
        history: History list from get_version_history()

    Returns:
        JSON string
    """
    return json.dumps({"versions": [asdict(v) for v in history]}, indent=2)


def write_history(db: VersionDatabase, output_format: str = "text", verbose: bool = False) -> None:
    """
    Write version history to stdout.

    Args:
        db: Database instance
        output_format: Output format ("text" or "json")
        verbose: Show detailed statistics
    """
    history = get_version_history(db, verbose)

    if output_format == "text":
        print(format_history_text(history, verbose))
    elif output_format == "json":
        print(format_history_json(history))
    else:
        raise ValueError(f"Invalid output format: {output_format}")
