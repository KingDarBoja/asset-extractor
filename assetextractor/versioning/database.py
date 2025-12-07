"""
Database schema and operations for asset versioning system.

This module provides the VersionDatabase class which manages:
- Database schema creation
- Version CRUD operations
- Asset lifecycle tracking
- Asset version history
- Statistics and queries
"""

import sqlite3
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict


@dataclass
class Version:
    """Represents a game version."""

    id: int
    version_string: str
    created_at: str
    description: str | None
    asset_count: int


@dataclass
class Asset:
    """Represents an asset lifecycle."""

    guid: int
    name: str | None
    template_name: str | None
    version_added: int
    version_deleted: int | None


@dataclass
class AssetVersion:
    """Represents an asset at a specific version."""

    id: int
    guid: int
    version_id: int
    xml_hash: str
    name: str | None
    template_name: str | None


class AssetVersionData(TypedDict):
    """Asset version data structure."""

    hash: str
    name: str | None
    template: str | None


class VersionStatistics(TypedDict):
    """Version statistics structure."""

    version_id: int
    version_string: str
    asset_count: int
    added: int
    changed: int
    deleted: int


class VersionDatabase:
    """Manages the SQLite database for asset versioning."""

    def __init__(self, db_path: Path | str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        if isinstance(db_path, str):
            db_path = Path(db_path)

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.create_schema()

    def create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()

        # versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_string TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                description TEXT,
                asset_count INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_string
            ON versions(version_string)
        """)

        # assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                guid INTEGER PRIMARY KEY,
                name TEXT,
                template_name TEXT,
                version_added INTEGER NOT NULL,
                version_deleted INTEGER,
                FOREIGN KEY (version_added) REFERENCES versions(id),
                FOREIGN KEY (version_deleted) REFERENCES versions(id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assets_version_added
            ON assets(version_added)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assets_version_deleted
            ON assets(version_deleted)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assets_template
            ON assets(template_name)
        """)

        # asset_versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid INTEGER NOT NULL,
                version_id INTEGER NOT NULL,
                xml_hash TEXT NOT NULL,
                name TEXT,
                template_name TEXT,
                FOREIGN KEY (guid) REFERENCES assets(guid),
                FOREIGN KEY (version_id) REFERENCES versions(id),
                UNIQUE(guid, version_id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_asset_versions_guid
            ON asset_versions(guid)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_asset_versions_version
            ON asset_versions(version_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_asset_versions_hash
            ON asset_versions(xml_hash)
        """)

        # metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Insert schema version if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO metadata (key, value)
            VALUES ('schema_version', '1')
        """)

        self.conn.commit()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions.

        Automatically commits on success, rolls back on exception.
        """
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    # Version operations

    def create_version(self, version_string: str, created_at: str, description: str | None, asset_count: int) -> int:
        """
        Create a new version record.

        Args:
            version_string: Version identifier (e.g., "1.0.0")
            created_at: ISO 8601 timestamp
            description: Optional version description
            asset_count: Total assets in this version

        Returns:
            Version ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO versions (version_string, created_at, description, asset_count)
            VALUES (?, ?, ?, ?)
        """,
            (version_string, created_at, description, asset_count),
        )
        version_id = cursor.lastrowid
        if version_id is None:
            raise RuntimeError("Failed to create version record")
        return version_id

    def get_version_by_string(self, version_string: str) -> Version | None:
        """
        Get version by version string.

        Args:
            version_string: Version identifier

        Returns:
            Version object or None if not found
        """
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM versions WHERE version_string = ?", (version_string,)).fetchone()

        if row is None:
            return None

        return Version(
            id=row["id"],
            version_string=row["version_string"],
            created_at=row["created_at"],
            description=row["description"],
            asset_count=row["asset_count"],
        )

    def get_version_by_id(self, version_id: int) -> Version | None:
        """
        Get version by ID.

        Args:
            version_id: Version ID

        Returns:
            Version object or None if not found
        """
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()

        if row is None:
            return None

        return Version(
            id=row["id"],
            version_string=row["version_string"],
            created_at=row["created_at"],
            description=row["description"],
            asset_count=row["asset_count"],
        )

    def get_latest_version_before(self, version_id: int) -> Version | None:
        """
        Get the latest version before the specified version.

        Args:
            version_id: Version ID

        Returns:
            Previous Version object or None if no previous version
        """
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT * FROM versions
            WHERE id < ?
            ORDER BY id DESC
            LIMIT 1
        """,
            (version_id,),
        ).fetchone()

        if row is None:
            return None

        return Version(
            id=row["id"],
            version_string=row["version_string"],
            created_at=row["created_at"],
            description=row["description"],
            asset_count=row["asset_count"],
        )

    def get_all_versions(self) -> list[Version]:
        """
        Get all versions ordered by ID.

        Returns:
            List of Version objects
        """
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT * FROM versions ORDER BY id").fetchall()

        return [
            Version(
                id=row["id"],
                version_string=row["version_string"],
                created_at=row["created_at"],
                description=row["description"],
                asset_count=row["asset_count"],
            )
            for row in rows
        ]

    def delete_version(self, version_id: int) -> None:
        """
        Delete a version and all associated data.

        Args:
            version_id: Version ID to delete
        """
        cursor = self.conn.cursor()

        # Delete asset_versions records
        cursor.execute("DELETE FROM asset_versions WHERE version_id = ?", (version_id,))

        # Reset version_deleted for assets that were deleted in this version
        cursor.execute("UPDATE assets SET version_deleted = NULL WHERE version_deleted = ?", (version_id,))

        # Delete assets that were added in this version (and not in any other version)
        cursor.execute(
            """
            DELETE FROM assets
            WHERE version_added = ?
            AND guid NOT IN (SELECT DISTINCT guid FROM asset_versions WHERE version_id != ?)
        """,
            (version_id, version_id),
        )

        # Delete version
        cursor.execute("DELETE FROM versions WHERE id = ?", (version_id,))

        self.conn.commit()

    # Asset operations

    def insert_asset(self, guid: int, name: str | None, template_name: str | None, version_added: int) -> None:
        """
        Insert a new asset record.

        Args:
            guid: Asset GUID
            name: Asset name
            template_name: Template name
            version_added: Version ID when asset was first added
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO assets (guid, name, template_name, version_added)
            VALUES (?, ?, ?, ?)
        """,
            (guid, name, template_name, version_added),
        )

    def update_asset(
        self, guid: int, name: str | None = None, template_name: str | None = None, version_deleted: int | None = None
    ) -> None:
        """
        Update asset record.

        Args:
            guid: Asset GUID
            name: Optional new name
            template_name: Optional new template name
            version_deleted: Optional version when deleted
        """
        updates: dict[str, str | int | None] = {}
        if name is not None:
            updates["name"] = name
        if template_name is not None:
            updates["template_name"] = template_name
        if version_deleted is not None:
            updates["version_deleted"] = version_deleted

        if not updates:
            return

        set_clause = ", ".join(f"{key} = ?" for key in updates)
        values: list[str | int | None] = [*list(updates.values()), guid]

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE assets SET {set_clause} WHERE guid = ?", values)

    def get_asset(self, guid: int) -> Asset | None:
        """
        Get asset by GUID.

        Args:
            guid: Asset GUID

        Returns:
            Asset object or None if not found
        """
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM assets WHERE guid = ?", (guid,)).fetchone()

        if row is None:
            return None

        return Asset(
            guid=row["guid"],
            name=row["name"],
            template_name=row["template_name"],
            version_added=row["version_added"],
            version_deleted=row["version_deleted"],
        )

    def get_asset_guids_in_version(self, version_id: int) -> set[int]:
        """
        Get all asset GUIDs present in a specific version.

        Args:
            version_id: Version ID

        Returns:
            Set of asset GUIDs
        """
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT guid FROM asset_versions WHERE version_id = ?", (version_id,)).fetchall()

        return {row["guid"] for row in rows}

    # Asset version operations

    def insert_asset_version(
        self, guid: int, version_id: int, xml_hash: str, name: str | None, template_name: str | None
    ) -> None:
        """
        Insert asset version record.

        Args:
            guid: Asset GUID
            version_id: Version ID
            xml_hash: SHA-256 hash of canonical XML
            name: Asset name
            template_name: Template name
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO asset_versions (guid, version_id, xml_hash, name, template_name)
            VALUES (?, ?, ?, ?, ?)
        """,
            (guid, version_id, xml_hash, name, template_name),
        )

    def get_asset_versions(self, version_id: int, template_filter: str | None = None) -> dict[int, AssetVersionData]:
        """
        Get all asset versions for a specific version.

        Args:
            version_id: Version ID
            template_filter: Optional template name filter

        Returns:
            Dict mapping GUID to asset version data
        """
        cursor = self.conn.cursor()

        if template_filter:
            rows = cursor.execute(
                """
                SELECT guid, xml_hash, name, template_name
                FROM asset_versions
                WHERE version_id = ? AND template_name = ?
            """,
                (version_id, template_filter),
            ).fetchall()
        else:
            rows = cursor.execute(
                """
                SELECT guid, xml_hash, name, template_name
                FROM asset_versions
                WHERE version_id = ?
            """,
                (version_id,),
            ).fetchall()

        return {
            row["guid"]: {"hash": row["xml_hash"], "name": row["name"], "template": row["template_name"]}
            for row in rows
        }

    def get_all_assets_in_version(
        self, version_id: int, template_filter: str | None = None
    ) -> dict[int, AssetVersionData]:
        """
        Get all assets that exist in a version, including unchanged assets.

        For assets without an asset_versions entry for this version,
        retrieves the most recent hash from a previous version.

        Args:
            version_id: Version ID
            template_filter: Optional template name filter

        Returns:
            Dict mapping GUID to asset data (hash, name, template)
        """
        cursor = self.conn.cursor()

        # Build template filter clause
        template_clause = "AND a.template_name = ?" if template_filter else ""
        params: list[int | str] = [version_id, version_id]
        if template_filter:
            params.append(template_filter)

        # Get all assets that exist in this version
        # (added before or in this version, and not deleted yet)
        query = f"""
            SELECT
                a.guid,
                a.name,
                a.template_name,
                (
                    SELECT av.xml_hash
                    FROM asset_versions av
                    WHERE av.guid = a.guid
                    AND av.version_id <= ?
                    ORDER BY av.version_id DESC
                    LIMIT 1
                ) as xml_hash
            FROM assets a
            WHERE a.version_added <= ?
            AND (a.version_deleted IS NULL OR a.version_deleted > ?)
            {template_clause}
        """

        params_with_version = [version_id, *params]

        rows = cursor.execute(query, params_with_version).fetchall()

        return {
            row["guid"]: {"hash": row["xml_hash"], "name": row["name"], "template": row["template_name"]}
            for row in rows
            if row["xml_hash"] is not None  # Skip assets with no hash history
        }

    def get_asset_version_history(self, guid: int) -> list[AssetVersion]:
        """
        Get version history for a specific asset.

        Args:
            guid: Asset GUID

        Returns:
            List of AssetVersion objects ordered by version ID
        """
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """
            SELECT * FROM asset_versions
            WHERE guid = ?
            ORDER BY version_id
        """,
            (guid,),
        ).fetchall()

        return [
            AssetVersion(
                id=row["id"],
                guid=row["guid"],
                version_id=row["version_id"],
                xml_hash=row["xml_hash"],
                name=row["name"],
                template_name=row["template_name"],
            )
            for row in rows
        ]

    # Statistics

    def get_version_statistics(self, version_id: int) -> VersionStatistics:
        """
        Get statistics for a version.

        Args:
            version_id: Version ID

        Returns:
            Dict with version stats (asset_count, added, changed, deleted)
        """
        # Get version info
        version = self.get_version_by_id(version_id)
        if version is None:
            raise ValueError(f"Version {version_id} not found")

        # Get previous version
        previous_version = self.get_latest_version_before(version_id)

        stats: VersionStatistics = {
            "version_id": version_id,
            "version_string": version.version_string,
            "asset_count": version.asset_count,
            "added": 0,
            "changed": 0,
            "deleted": 0,
        }

        if previous_version is None:
            # First version - all assets are added
            stats["added"] = version.asset_count
            return stats

        # Get asset versions for current and previous version
        current_assets = self.get_asset_versions(version_id)
        previous_assets = self.get_asset_versions(previous_version.id)

        current_guids = set(current_assets.keys())
        previous_guids = set(previous_assets.keys())

        # Calculate changes
        stats["added"] = len(current_guids - previous_guids)
        stats["deleted"] = len(previous_guids - current_guids)

        # Count changed assets (different hash)
        for guid in current_guids & previous_guids:
            if current_assets[guid]["hash"] != previous_assets[guid]["hash"]:
                stats["changed"] += 1

        return stats

    def execute_with_retry[T](self, func: Callable[[], T], max_retries: int = 3) -> T:
        """
        Execute a database operation with retry on lock.

        Args:
            func: Function to execute
            max_retries: Maximum retry attempts

        Returns:
            Function result

        Raises:
            Exception if all retries fail
        """
        for attempt in range(max_retries):
            try:
                return func()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    sleep_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(sleep_time)
                else:
                    raise
        raise RuntimeError("Unreachable code")

    def __enter__(self) -> "VersionDatabase":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> bool:
        """Context manager exit."""
        self.close()
        return False
