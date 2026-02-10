"""
Extracts item data from Anno 117, including icons, and uploads it to a Google Sheet
with separate tabs for English and German.
"""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from pathlib import Path

import gspread  # type: ignore
import pandas as pd  # type: ignore
from google.oauth2.service_account import Credentials  # type: ignore
from gspread_dataframe import set_with_dataframe  # type: ignore
from wand.image import Image  # type: ignore

from assetextractor.conversion.statistics.item_extractor import ItemExtractor
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import Asset, AssetCache

# --- Configuration ---
# The name of the Google Sheet you want to create or overwrite.
# Note: Google Sheets API identifies sheets by name. If you have multiple sheets with the same name,
# it's best to use a unique name to avoid ambiguity. The concept of a folder path like
# 'public/Anno 117/tables/Items' does not directly translate. Please use the exact
# name of the sheet as it appears in Google Drive.
GOOGLE_SHEET_NAME = "Items"  # Name of the Google Sheet to create/use
CREDENTIALS_FILE = Path(__file__) / "../../../../gsheet_credentials.json"  # Path to your credentials
LANGUAGES = ["english", "german"]

ICON_OUTPUT_DIR = Path(__file__).parent.parent.parent / "results/tables/icons"


def save_icon_and_get_filename(asset: Asset | None, cache: dict[str, str], resize_factor: int = 8) -> str | None:
    """Saves a resized asset's icon locally and returns the filename, using a cache."""
    if asset is None:
        return None

    icon = asset.icon
    if icon is None or icon.value is None:
        return None

    icon_path: str = icon.canonical_name
    if icon_path in cache:
        return cache[icon_path]

    try:
        # Use a more generic name for the icon file, based on its own filename
        # This is better for caching, as different items can share the same icon.
        output_filename = f"{icon_path}.webp"
        output_path = ICON_OUTPUT_DIR / output_filename

        # Check if file already exists
        if output_path.exists():
            cache[icon_path] = output_filename
            return output_filename

        ICON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        img_data = icon.get_image()
        if img_data is not None:
            with Image(img_data) as img:
                img.resize(width=img.width // resize_factor, height=img.height // resize_factor)
                img.format = "webp"
                img.save(filename=str(output_path))
                print(output_path)

        cache[icon_path] = output_filename
        return output_filename
    except Exception as e:
        print(f"Could not process icon for {asset.name}: {e}")
        return None


def main():
    """Main function to extract and upload item data."""
    # --- Authenticate with Google Sheets ---
    print("Authenticating with Google Sheets...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scope)
    gc = gspread.authorize(credentials)
    print("Authentication successful.")

    # --- Load Assets ---
    print("Loading assets...")
    config = Config.from_json(Path(__file__).parent / "../../../config.json")
    assets = AssetCache.load(config)

    # --- Create or Open Spreadsheet ---
    try:
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        print(f"Opened existing spreadsheet: '{GOOGLE_SHEET_NAME}'")
    except gspread.exceptions.SpreadsheetNotFound:
        spreadsheet = gc.create(GOOGLE_SHEET_NAME)
        print(f"Created new spreadsheet: '{GOOGLE_SHEET_NAME}'")
        # Share with yourself to have access
        spreadsheet.share("user@example.com", perm_type="user", role="writer")

    for lang in LANGUAGES:
        print(f"--- Processing language: {lang} ---")

        # 1. Extract items
        extractor = ItemExtractor(assets, language=lang)
        items_data = extractor.extract_all_items()
        df = pd.DataFrame(items_data)

        # 2. Add icon column - Icons won't load
        # print('Adding item icons...')
        # df['icon'] = df['guid'].apply(lambda guid: save_icon_and_get_filename(assets.get(guid), icon_cache))

        # 3. Reorder columns
        cols = [
            "guid",
            "name",
            "rarity",
            "niche",
            "trade_price",
            "targets",
            "buffs",
            "boost_condition",
            "boost_buffs",
            "source",
        ]
        df = df[cols]

        # 4. Upload to Google Sheet
        print(f"Uploading {len(df)} items to worksheet: {lang}")
        try:
            worksheet = spreadsheet.worksheet(lang)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=lang, rows=100, cols=20)

        set_with_dataframe(worksheet, df)
        print("Done.")

    print(f"\nSuccessfully updated Google Sheet: {spreadsheet.url}")


if __name__ == "__main__":
    main()
