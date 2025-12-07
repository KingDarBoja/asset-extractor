"""
Asset versioning system for tracking Anno 117 asset changes across game versions.

This module provides functionality to:
- Create version snapshots with XML hashing
- Compare versions to detect added/changed/deleted assets
- Export version data to CSV/JSON
- Query version history with statistics
"""

from assetextractor.versioning.database import VersionDatabase

__all__ = ["VersionDatabase"]
