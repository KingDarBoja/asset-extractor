"""
Test case to validate item extraction accuracy against manually corrected CSV.

This test compares the output of extract_items.ipynb with the manually corrected
CSV file to identify differences and guide incremental improvements to the extraction logic.
"""

import csv
import pytest
from pathlib import Path
from typing import Any

from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache


# Paths to compare
MANUAL_CSV_PATH = Path("results/tables/items_english_v1.3_manual_corrections.csv")
GENERATED_CSV_PATH = Path("results/tables/items_english.csv")


class ItemDifference:
    """Represents a difference between manual and generated item data."""

    def __init__(self, guid: str, item_name: str, column: str, manual_value: str, generated_value: str):
        self.guid = guid
        self.item_name = item_name
        self.column = column
        self.manual_value = manual_value
        self.generated_value = generated_value

    def __str__(self):
        return (
            f"\nItem: {self.item_name} (GUID: {self.guid})\n"
            f"  Column: {self.column}\n"
            f"  Manual:    {self.manual_value[:100]}{'...' if len(self.manual_value) > 100 else ''}\n"
            f"  Generated: {self.generated_value[:100]}{'...' if len(self.generated_value) > 100 else ''}"
        )

    def __repr__(self):
        return self.__str__()


def load_csv_to_dict(csv_path: Path) -> dict[str, dict[str, str]]:
    """Load CSV file into a dictionary keyed by GUID."""
    items = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            guid = row["guid"]
            items[guid] = row
    return items


def normalize_value(value: str) -> str:
    """Normalize a CSV value for comparison."""
    if not value:
        return ""
    # Strip whitespace
    value = value.strip()
    # Normalize multiple spaces
    value = " ".join(value.split())
    return value


def compare_items(manual_items: dict, generated_items: dict) -> dict[str, list[ItemDifference]]:
    """
    Compare manual and generated items, returning differences grouped by column.

    Returns:
        Dictionary mapping column names to lists of ItemDifference objects
    """
    differences_by_column = {
        "name": [],
        "rarity": [],
        "selling price": [],
        "affected buildings": [],
        "effects": [],
        "boost condition": [],
        "boosted effects": [],
        "source": []
    }

    # Map generated column names to manual column names
    column_mapping = {
        "name": "name",
        "rarity": "rarity",
        "trade_price": "selling price",
        "targets": "affected buildings",
        "buffs": "effects",
        "boost_condition": "boost condition",
        "boost_buffs": "boosted effects",
        "source": "source"
    }

    # Compare each item in manual CSV
    for guid, manual_item in manual_items.items():
        if guid not in generated_items:
            # Item missing in generated data
            for column in differences_by_column.keys():
                diff = ItemDifference(
                    guid=guid,
                    item_name=manual_item["name"],
                    column=column,
                    manual_value=manual_item.get(column, ""),
                    generated_value="MISSING ITEM"
                )
                differences_by_column[column].append(diff)
            continue

        generated_item = generated_items[guid]

        # Compare each column
        for gen_col, manual_col in column_mapping.items():
            manual_val = normalize_value(manual_item.get(manual_col, ""))
            generated_val = normalize_value(generated_item.get(gen_col, ""))

            if manual_val != generated_val:
                diff = ItemDifference(
                    guid=guid,
                    item_name=manual_item["name"],
                    column=manual_col,
                    manual_value=manual_val,
                    generated_value=generated_val
                )
                differences_by_column[manual_col].append(diff)

    return differences_by_column


def save_differences_report(differences: dict[str, list[ItemDifference]], output_path: Path):
    """Save a detailed report of all differences to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("="*100 + "\n")
        f.write("ITEM EXTRACTION ACCURACY REPORT\n")
        f.write("="*100 + "\n\n")

        total_differences = sum(len(diffs) for diffs in differences.values())
        f.write(f"Total differences: {total_differences}\n\n")

        for column, diffs in differences.items():
            if diffs:
                f.write("\n" + "="*100 + "\n")
                f.write(f"{column.upper()}: {len(diffs)} differences\n")
                f.write("="*100 + "\n\n")

                for i, diff in enumerate(diffs, 1):
                    f.write(f"{i}. Item: {diff.item_name} (GUID: {diff.guid})\n")
                    f.write(f"   Manual:    {diff.manual_value}\n")
                    f.write(f"   Generated: {diff.generated_value}\n")
                    f.write("\n")


def test_item_extraction_accuracy():
    """
    Compare generated item extraction with manually corrected CSV.

    This test will fail initially, showing all differences. As the extraction
    code is improved, the number of differences should decrease.
    """
    # Check that both files exist
    assert MANUAL_CSV_PATH.exists(), f"Manual CSV not found: {MANUAL_CSV_PATH}"

    # Load both CSVs
    manual_items = load_csv_to_dict(MANUAL_CSV_PATH)

    # Generate items if CSV doesn't exist
    if not GENERATED_CSV_PATH.exists():
        pytest.skip(f"Generated CSV not found: {GENERATED_CSV_PATH}. Run extract_items.ipynb first.")

    generated_items = load_csv_to_dict(GENERATED_CSV_PATH)

    # Compare
    differences = compare_items(manual_items, generated_items)

    # Save detailed report
    report_path = Path("results/test_reports/item_extraction_differences.txt")
    save_differences_report(differences, report_path)

    # Print summary statistics
    print("\n" + "="*80)
    print("ITEM EXTRACTION ACCURACY TEST RESULTS")
    print("="*80)
    print(f"\nTotal items in manual CSV: {len(manual_items)}")
    print(f"Total items in generated CSV: {len(generated_items)}")

    print("\n" + "-"*80)
    print("DIFFERENCES BY COLUMN:")
    print("-"*80)

    total_differences = 0
    for column, diffs in differences.items():
        if diffs:
            total_differences += len(diffs)
            print(f"\n{column.upper()}: {len(diffs)} differences")

    print("\n" + "-"*80)
    print(f"TOTAL DIFFERENCES: {total_differences}")
    print("-"*80)

    if total_differences > 0:
        print(f"\nDetailed report saved to: {report_path.absolute()}")

    # Show sample differences for each column (first 3)
    for column, diffs in differences.items():
        if diffs:
            print(f"\n{'='*80}")
            print(f"SAMPLE DIFFERENCES: {column.upper()} (showing first 3 of {len(diffs)})")
            print('='*80)
            for diff in diffs[:3]:
                print(diff)

    # Assert: The test should pass when there are no differences
    if total_differences > 0:
        pytest.fail(
            f"\n\n{total_differences} differences found between manual and generated CSVs.\n"
            f"See detailed output above for sample differences in each column.\n"
            f"Detailed report saved to: {report_path.absolute()}\n"
            f"Fix the extraction code incrementally to reduce these differences."
        )


def test_column_name_mapping():
    """Verify that column names are correctly mapped."""
    manual_items = load_csv_to_dict(MANUAL_CSV_PATH)

    # Get first item to check columns
    first_item = next(iter(manual_items.values()))

    expected_columns = {
        "guid",
        "name",
        "rarity",
        "selling price",
        "affected buildings",
        "effects",
        "boost condition",
        "boosted effects",
        "source"
    }

    actual_columns = set(first_item.keys())

    assert actual_columns == expected_columns, (
        f"Column mismatch!\n"
        f"Expected: {expected_columns}\n"
        f"Actual: {actual_columns}\n"
        f"Missing: {expected_columns - actual_columns}\n"
        f"Extra: {actual_columns - expected_columns}"
    )


def test_all_manual_items_present():
    """Verify that all items from manual CSV are present in generated CSV."""
    manual_items = load_csv_to_dict(MANUAL_CSV_PATH)

    if not GENERATED_CSV_PATH.exists():
        pytest.skip(f"Generated CSV not found: {GENERATED_CSV_PATH}")

    generated_items = load_csv_to_dict(GENERATED_CSV_PATH)

    missing_items = []
    for guid, item in manual_items.items():
        if guid not in generated_items:
            missing_items.append(f"{item['name']} (GUID: {guid})")

    if missing_items:
        pytest.fail(
            f"\n{len(missing_items)} items from manual CSV are missing in generated CSV:\n" +
            "\n".join(f"  - {item}" for item in missing_items[:10]) +
            (f"\n  ... and {len(missing_items) - 10} more" if len(missing_items) > 10 else "")
        )


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
