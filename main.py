import argparse
import sys
from pathlib import Path

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.conversion.assetbrowser.convert import Converter
from assetextractor.versioning.snapshot import create_snapshot
from assetextractor.versioning.report import generate_version_report


def main():
    parser = argparse.ArgumentParser(description="Asset Extractor - Generate asset browser")
    parser.add_argument(
        "--version",
        help="Version string (e.g., '1.0.0'). If provided, creates a snapshot and generates a version report.",
    )
    parser.add_argument(
        "--prev-version",
        help="Previous version for comparison report (defaults to previous snapshot in database)",
    )
    parser.add_argument("--config", default="config.json", help="Path to config.json (default: config.json)")
    parser.add_argument(
        "--db", default="versioning/anno117/assets.db", help="Path to database (default: versioning/anno117/assets.db)"
    )

    args = parser.parse_args()

    # Load config
    config = Config.from_json(args.config)

    # Load assets once
    print("Loading assets...")
    assets = AssetCache.load(config)
    print(f"Loaded {len(assets.elements):,} assets")

    # Generate asset browser
    print("\nGenerating asset browser...")
    Converter(assets, config).run()
    print(f"Asset browser generated at: {config.assetbrowser_dir}")

    # If version specified, create snapshot and report
    if args.version:
        print(f"\nCreating snapshot '{args.version}'...")
        db_path = Path(args.db)

        # Create snapshot
        stats = create_snapshot(
            config=config,
            version_string=args.version,
            db_path=db_path,
            description=None,
            force=False,
            assets=assets,  # Reuse already-loaded assets
        )

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

        # Generate version report if there's a previous version
        from assetextractor.versioning.database import VersionDatabase

        db = VersionDatabase(db_path)
        versions = db.get_all_versions()
        db.close()

        if len(versions) >= 2:
            # Find previous version
            if args.prev_version:
                prev_version = args.prev_version
            else:
                # Use the second-to-last version
                prev_version = versions[-2].version_string

            print(f"\nGenerating version report comparing '{prev_version}' to '{args.version}'...")
            report_path = generate_version_report(
                db_path=db_path,
                version1_str=prev_version,
                version2_str=args.version,
                output_dir=config.assetbrowser_dir,
                config=config,
            )
            print(f"Version report generated: {report_path}")
        else:
            print("\nSkipping version report (no previous version to compare against)")

    return 0


if __name__ == "__main__":
    sys.exit(main())