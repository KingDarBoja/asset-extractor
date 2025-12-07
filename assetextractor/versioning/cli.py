"""
Command-line interface for asset versioning system.

This module provides the main entry point for the versioning system with commands:
- snapshot: Create version snapshot
- diff: Compare two versions
- export: Export version data
- history: Show version history

Usage:
    python -m assetextractor.versioning [command] [options]
"""

import argparse
import sys
from pathlib import Path

from assetextractor.extraction.utils import Config
from assetextractor.versioning.database import VersionDatabase
from assetextractor.versioning.diff import compare_versions, write_diff
from assetextractor.versioning.export import export_versions
from assetextractor.versioning.history import write_history
from assetextractor.versioning.snapshot import create_snapshot


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Handle snapshot command."""
    try:
        # Load config
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Config file not found at {config_path}")
            print("Please create a config file using config.template.json")
            return 1

        config = Config.from_json(config_path)

        # Create snapshot
        print(f"Creating snapshot '{args.version}'...")
        stats = create_snapshot(
            config=config,
            version_string=args.version,
            db_path=Path(args.db),
            description=args.description,
            force=args.force,
        )

        # Print results
        print("")
        print("=" * 60)
        print(f"Snapshot '{stats['version_string']}' created successfully!")
        print("")
        print(f"  Total Assets:  {stats['asset_count']:,}")
        if stats["added"] > 0:
            print(f"  Added:         {stats['added']:,}")
        if stats["changed"] > 0:
            print(f"  Changed:       {stats['changed']:,}")
        if stats["deleted"] > 0:
            print(f"  Deleted:       {stats['deleted']:,}")
        print(f"  Duration:      {stats['duration_seconds']:.1f}s")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_diff(args: argparse.Namespace) -> int:
    """Handle diff command."""
    try:
        db = VersionDatabase(Path(args.db))

        # Compare versions
        diff = compare_versions(
            db=db, version1_str=args.version1, version2_str=args.version2, template_filter=args.template
        )

        # Write output
        output_path = Path(args.output) if args.output else None
        write_diff(diff=diff, output_format=args.format, output_path=output_path, verbose=args.verbose)

        db.close()
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Handle export command."""
    try:
        db = VersionDatabase(Path(args.db))

        # Export data
        export_versions(
            db=db,
            output_path=Path(args.output),
            output_format=args.format,
            version=args.version,
            changes_only=args.changes_only,
            template_filter=args.template,
        )

        db.close()
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_history(args: argparse.Namespace) -> int:
    """Handle history command."""
    try:
        db = VersionDatabase(Path(args.db))

        # Write history
        write_history(db=db, output_format=args.format, verbose=args.verbose)

        db.close()
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """Handle report command."""
    try:
        # Load config if provided
        config = None
        if args.config:
            config_path = Path(args.config)
            if config_path.exists():
                config = Config.from_json(config_path)
            else:
                print(f"Warning: Config not found at {config_path}, proceeding without asset names")

        # Generate report
        from assetextractor.versioning.report import generate_version_report

        output_path = generate_version_report(
            db_path=Path(args.db),
            version1_str=args.version1,
            version2_str=args.version2,
            output_dir=Path(args.output),
            config=config,
        )

        print(f"\nHTML report generated: {output_path}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Asset versioning system for Anno 117",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create initial snapshot
  python -m assetextractor.versioning snapshot "1.0.0" --description "Launch version"

  # Create snapshot after game update
  python -m assetextractor.versioning snapshot "1.0.1"

  # Compare two versions
  python -m assetextractor.versioning diff "1.0.0" "1.0.1"

  # Export only items that changed
  python -m assetextractor.versioning diff "1.0.0" "1.0.1" --template Item --format json --output changes.json

  # View version history
  python -m assetextractor.versioning history --verbose

  # Export all data to CSV
  python -m assetextractor.versioning export --output all_versions.csv
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Snapshot command
    parser_snapshot = subparsers.add_parser(
        "snapshot", help="Create a version snapshot", description="Create a new version snapshot of all assets"
    )
    parser_snapshot.add_argument("version", help="Version identifier (e.g., '1.0.0', 'Season 2')")
    parser_snapshot.add_argument("--config", default="config.json", help="Path to config.json (default: config.json)")
    parser_snapshot.add_argument(
        "--db", default="versioning/anno117/assets.db", help="Path to database (default: versioning/anno117/assets.db)"
    )
    parser_snapshot.add_argument("--description", help="Optional version description")
    parser_snapshot.add_argument(
        "--force", action="store_true", help="Overwrite existing version (default: error if exists)"
    )
    parser_snapshot.set_defaults(func=cmd_snapshot)

    # Diff command
    parser_diff = subparsers.add_parser(
        "diff", help="Compare two versions", description="Compare two versions and show changes"
    )
    parser_diff.add_argument("version1", help="First version (older)")
    parser_diff.add_argument("version2", help="Second version (newer)")
    parser_diff.add_argument(
        "--db", default="versioning/anno117/assets.db", help="Path to database (default: versioning/anno117/assets.db)"
    )
    parser_diff.add_argument("--template", help="Filter by template name (e.g., 'Item', 'BuildingBuff')")
    parser_diff.add_argument(
        "--format", choices=["text", "json", "csv"], default="text", help="Output format (default: text)"
    )
    parser_diff.add_argument("--output", help="Write to file instead of stdout")
    parser_diff.add_argument("--verbose", action="store_true", help="Show detailed changes (GUIDs, hashes)")
    parser_diff.set_defaults(func=cmd_diff)

    # Export command
    parser_export = subparsers.add_parser(
        "export", help="Export version data", description="Export version data to CSV or JSON"
    )
    parser_export.add_argument("--output", required=True, help="Output file path")
    parser_export.add_argument(
        "--db", default="versioning/anno117/assets.db", help="Path to database (default: versioning/anno117/assets.db)"
    )
    parser_export.add_argument("--version", help="Export specific version (default: all versions)")
    parser_export.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format (default: csv)")
    parser_export.add_argument(
        "--changes-only", action="store_true", help="Export only assets with changes (excludes unchanged)"
    )
    parser_export.add_argument("--template", help="Filter by template name")
    parser_export.set_defaults(func=cmd_export)

    # History command
    parser_history = subparsers.add_parser(
        "history", help="Show version history", description="Display version history with statistics"
    )
    parser_history.add_argument(
        "--db", default="versioning/anno117/assets.db", help="Path to database (default: versioning/anno117/assets.db)"
    )
    parser_history.add_argument("--verbose", action="store_true", help="Show detailed statistics per version")
    parser_history.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )
    parser_history.set_defaults(func=cmd_history)

    # Report command
    parser_report = subparsers.add_parser(
        "report",
        help="Generate HTML version report",
        description="Generate HTML report comparing two versions with asset browser links",
    )
    parser_report.add_argument("version1", help="First version (older)")
    parser_report.add_argument("version2", help="Second version (newer)")
    parser_report.add_argument(
        "--db", default="versioning/anno117/assets.db", help="Path to database (default: versioning/anno117/assets.db)"
    )
    parser_report.add_argument(
        "--output", default="results/assetbrowser/", help="Output directory (default: results/assetbrowser/)"
    )
    parser_report.add_argument(
        "--config", default="config.json", help="Config file for asset names (default: config.json)"
    )
    parser_report.set_defaults(func=cmd_report)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
