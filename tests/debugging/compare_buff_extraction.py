"""Compare old manual buff extraction with new buff_ui property."""

import subprocess
import sys
from pathlib import Path

def run_notebook(notebook_path: Path, output_name: str):
    """Run a Jupyter notebook and convert to Python script to execute."""
    print(f"\n{'='*80}")
    print(f"Running: {notebook_path.name}")
    print(f"{'='*80}\n")

    # Convert notebook to Python script
    temp_script = notebook_path.with_suffix('.temp.py')
    subprocess.run([
        'jupyter', 'nbconvert', '--to', 'script',
        '--output', temp_script.stem,
        str(notebook_path)
    ], check=True)

    # Run the script
    subprocess.run([sys.executable, str(temp_script)], check=True)

    # Clean up temp script
    temp_script.unlink()

    print(f"\n✓ Completed: {notebook_path.name}")


def compare_outputs():
    """Compare the two output CSV files."""
    import pandas as pd
    import difflib

    old_file = Path("results/items.csv")
    new_file = Path("results/items_v2.csv")

    if not old_file.exists():
        print(f"\n⚠ Old output file not found: {old_file}")
        print("Run the original notebook first to generate it.")
        return

    if not new_file.exists():
        print(f"\n⚠ New output file not found: {new_file}")
        return

    print(f"\n{'='*80}")
    print("Comparing Output Files")
    print(f"{'='*80}\n")

    # Load both CSVs
    df_old = pd.read_csv(old_file)
    df_new = pd.read_csv(new_file)

    print(f"Old version: {len(df_old)} items")
    print(f"New version: {len(df_new)} items")

    # Compare row counts
    if len(df_old) != len(df_new):
        print(f"\n⚠ WARNING: Different number of items!")
    else:
        print(f"✓ Same number of items")

    # Compare a sample of buff descriptions
    print(f"\n{'='*80}")
    print("Sample Comparison (first 5 items with buffs)")
    print(f"{'='*80}\n")

    for idx in range(min(5, len(df_old))):
        old_buff = df_old.iloc[idx]['buffs']
        new_buff = df_new.iloc[idx]['buffs']
        item_name = df_old.iloc[idx]['name']

        if old_buff or new_buff:
            print(f"\nItem: {item_name}")
            print(f"  Old: {old_buff}")
            print(f"  New: {new_buff}")

            if old_buff == new_buff:
                print(f"  ✓ IDENTICAL")
            else:
                print(f"  ⚠ DIFFERENT")
                # Show diff
                diff = list(difflib.unified_diff(
                    [old_buff], [new_buff],
                    lineterm='',
                    fromfile='old',
                    tofile='new'
                ))
                for line in diff[2:]:  # Skip the file headers
                    print(f"    {line}")

    # Full diff to file
    diff_file = Path("results/buff_extraction_diff.txt")
    diff_file.parent.mkdir(parents=True, exist_ok=True)

    with open(diff_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Full Comparison of Buff Extraction Methods\n")
        f.write("="*80 + "\n\n")

        differences = 0
        for idx in range(len(df_old)):
            old_buff = df_old.iloc[idx]['buffs']
            new_buff = df_new.iloc[idx]['buffs']
            item_name = df_old.iloc[idx]['name']
            guid = df_old.iloc[idx]['guid']

            if old_buff != new_buff:
                differences += 1
                f.write(f"\n{'='*80}\n")
                f.write(f"Item #{idx + 1}: {item_name} (GUID: {guid})\n")
                f.write(f"{'='*80}\n")
                f.write(f"OLD: {old_buff}\n")
                f.write(f"NEW: {new_buff}\n")

                # Show character-level diff
                diff = list(difflib.unified_diff(
                    old_buff.split(';'),
                    new_buff.split(';'),
                    lineterm=''
                ))
                if diff:
                    f.write(f"\nDIFF:\n")
                    for line in diff:
                        f.write(f"  {line}\n")

        f.write(f"\n{'='*80}\n")
        f.write(f"Summary: {differences} items with different buff descriptions out of {len(df_old)} total\n")
        f.write(f"{'='*80}\n")

    print(f"\n{'='*80}")
    print(f"✓ Full diff saved to: {diff_file.absolute()}")
    print(f"  Total differences: {differences} / {len(df_old)} items")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Note: This script expects notebooks to be run manually or via jupyter
    # For now, just compare if both files exist
    compare_outputs()
