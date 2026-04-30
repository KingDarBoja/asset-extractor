import pytest
from assetextractor.parsing.core.assets import AssetCache

def test_dlc_unlock_detection(assets: AssetCache):
    """Test that DLC unlock detection works for various strategies."""
    
    # Strategy 7/8: Patron -> Items (Vulcan example)
    # PatronVulcanus (144800) should be DLC01 (67902)
    vulcan = assets.elements.get(144800)
    assert vulcan is not None
    assert 67902 in vulcan.unlocked_by_dlcs
    
    # Strategy 1b/1c: Egyptian Good (Dates example)
    # Good Egyptian Dates (151680) should be DLC03 (67904)
    dates = assets.elements.get(151680)
    assert dates is not None
    assert 67904 in dates.unlocked_by_dlcs
    
    # Strategy 1: Icon path
    # Some dlc01 icon asset
    # Let's find one that has /dlc01/ in its icon path
    dlc01_assets = [a for a in assets.elements.values() 
                    if a.icon and "/dlc01/" in str(a.icon.value).lower().replace("\\", "/")]
    if dlc01_assets:
        for a in dlc01_assets:
            # Skip if it's hall_of_fame
            if "hall_of_fame" in str(a.icon.value).lower():
                continue
            assert 67902 in a.unlocked_by_dlcs
            
    # Strategy 2: UplayProductUnlocks
    # Check DLC01 cosmestics if any
    dlc01 = assets.elements.get(67902)
    if dlc01:
        unlocks = dlc01.dlc_unlocks
        assert len(unlocks) > 0
        for ref in unlocks.values():
            assert 67902 in ref.source.unlocked_by_dlcs

def test_dlc_bidirectional_references(assets: AssetCache):
    """Test that DLC references are correctly populated in both directions."""
    # Find any asset with DLC unlocks
    dlc_tagged_assets = [a for a in assets.elements.values() if a.unlocked_by_dlcs]
    assert len(dlc_tagged_assets) > 0
    
    for asset in dlc_tagged_assets[:10]: # Check first 10
        for dlc_guid, ref in asset.unlocked_by_dlcs.items():
            dlc_asset = ref.source
            assert dlc_guid == dlc_asset.guid
            assert asset.guid in dlc_asset.dlc_unlocks
            assert dlc_asset.dlc_unlocks[asset.guid].source == asset
