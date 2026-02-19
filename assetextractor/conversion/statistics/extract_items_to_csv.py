"""
Extracts item data from Anno 117 and saves it to a versioned CSV file.
"""

import argparse
from pathlib import Path

from assetextractor.conversion.statistics.item_extractor import ItemExtractor
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

OUTPUT_DIR = Path(__file__).parent.parent.parent / "results/tables"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export items to CSV")
    parser.add_argument("--version", required=True, help="Version number (e.g. 1.0.1)")
    args = parser.parse_args()

    config = Config.from_json(Path(__file__).parent / "../../../config.json")
    assets = AssetCache.load(config)

    extractor = ItemExtractor(assets, language="english")
    items_data = extractor.extract_all_items()

    output_path = OUTPUT_DIR / f"items_english_{args.version}.csv"
    extractor.save_to_csv(items_data, output_path)


if __name__ == "__main__":
    main()
