import json
import os

notebook_path = os.path.join('assetextractor', 'conversion', 'statistics', 'extract_items_to_gsheet.ipynb')

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        json.load(f)
    print("JSON is valid.")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
except FileNotFoundError:
    print(f"File not found: {notebook_path}")
