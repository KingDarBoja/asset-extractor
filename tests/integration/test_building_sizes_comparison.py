import json
import pytest
import importlib
from pathlib import Path

# Dynamic import because of the hyphen in the filename
building_sizes_module = importlib.import_module("assetextractor.conversion.calculator.building-sizes")
Converter = building_sizes_module.Converter

@pytest.fixture
def presets_data():
    """Load the presets data from the JSON file."""
    presets_path = Path("tests/integration/presets.json")
    if not presets_path.exists():
        pytest.skip(f"Presets file not found at {presets_path}")
        
    with open(presets_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_building_sizes_match_presets(assets, presets_data):
    """
    Compare calculated building sizes with those in presets.json.
    Ignores if x and z dimensions are swapped.
    """
    # Initialize Converter with the shared assets cache
    converter = Converter(assets)
    
    failures = []
    
    # Prepare list of assets to process
    assets_to_process = []
    guid_to_preset = {}
    
    for building in presets_data.get("Buildings", []):
        guid = building.get("Guid")
        
        # Skip if GUID is missing or 0
        if not guid:
            continue
            
        # Get the asset from the cache
        try:
            asset = assets[guid]
            assets_to_process.append(asset)
            guid_to_preset[guid] = building
        except KeyError:
            # Asset might not exist in the current game version or cache
            # This is expected if presets.json contains items from a different version/DLC not present locally
            # We'll just skip it for now to avoid false positives
            pass
            
    # Batch process all found assets
    converter.process_assets(assets_to_process)
    
    # Check results
    for asset in assets_to_process:
        guid = asset.guid
        building = guid_to_preset[guid]
        
        expected_x = building.get("BuildBlocker", {}).get("x")
        expected_z = building.get("BuildBlocker", {}).get("z")
        
        # Retrieve the calculated size
        calculated_size = converter.building_sizes.get(guid)
        
        if calculated_size is None:
            # Check why it was not calculated
            # It could be excluded
            should_exclude, reason = converter.should_exclude_asset(asset)
            if should_exclude:
                # If it's excluded in our logic but present in presets, we might want to know
                # But for now, if our logic explicitly excludes it (e.g. "Test"), we accept that difference
                # unless it's a valid building.
                # Let's log it if it's not a generic exclusion
                pass
            else:
                 # If not excluded but missing, it's an error
                 error = next((e for e in converter.errors if e.guid == guid), None)
                 if error:
                     failures.append(f"GUID {guid} ({building.get('Identifier')}): Calculation failed - {error.category} {error.details}")
                 else:
                     failures.append(f"GUID {guid} ({building.get('Identifier')}): Unknown reason for missing size.")
            continue
            
        calc_x, calc_z = calculated_size
        
        # Check match, allowing swap
        # Some items in presets might have x=0 z=0 which usually means unblocked or special
        # If our calculator returns 1x1 (default) for those, we might have a mismatch
        
        matches = (calc_x == expected_x and calc_z == expected_z) or \
                  (calc_x == expected_z and calc_z == expected_x)
                  
        if not matches:
            failures.append(
                f"GUID {guid} ({building.get('Identifier')}): "
                f"Expected {expected_x}x{expected_z} (or swapped), "
                f"Got {calc_x}x{calc_z}"
            )

    # Report failures
    if failures:
        failure_msg = f"Found {len(failures)} mismatches between calculated sizes and presets.json:\n"
        failure_msg += "\n".join(failures[:20]) # Show first 20
        if len(failures) > 20:
            failure_msg += f"\n... and {len(failures) - 20} more."
        pytest.fail(failure_msg)
