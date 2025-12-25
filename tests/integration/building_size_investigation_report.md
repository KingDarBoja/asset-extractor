# Buildings with Zero Dimensions Investigation Report

**Status: FIXED** ✓

## Summary

All 21 buildings that previously had zero dimensions have been fixed. The issue was caused by BoundingBox/Extents values being in physical units (meters) rather than grid cells. Small values (< 0.5 meters) rounded to 0, creating invalid sizes like (0, 0), (0, 1), or (1, 0).

### Root Cause

Buildings without BuildBlocker data (which provides grid coordinates) fall back to BoundingBox/Extents for size extraction. However:
- BoundingBox/Extents are in **physical units (meters)**, not grid cells
- Small ornaments and walls have physical dimensions < 1.0 meter
- When rounded to integers, these become 0, creating invalid sizes

### Fix Applied

**File:** `assetextractor/conversion/calculator/building-sizes.py`

1. **BoundingBox validation**: After extracting from BoundingBox/Extents, check if either dimension is 0. If so, don't return immediately - fall through to filename and asset name extraction strategies.

2. **Modular infrastructure**: Added `MilitaryWall` template to the modular infrastructure list. These buildings default to (1, 1) without logging errors.

3. **Fallback chain**: Buildings now use this priority:
   - BuildBlocker corners (most accurate)
   - BoundingBox/Extents (if both dimensions > 0)
   - Filename pattern (e.g., "1x1", "2x2")
   - Asset name pattern (e.g., "Ornament 1x1")
   - Modular infrastructure default (1x1)

### Results

- **Before:** 21 buildings with zero dimensions, 13 errors
- **After:** 0 buildings with zero dimensions, 8 errors (different issues)

All previously problematic buildings now have valid (1, 1) sizes.

---

## Original Investigation Data (2025-12-25)

Total buildings with zero dimensions (before fix): 21


## MilitaryTowerUnit: 1 buildings

| GUID | Size | Internal Name | English Name | IFO Source | BoundingBox | BuildBlocker |
|------|------|---------------|--------------|------------|-------------|-------------|
| 54954 | 0x0 | Harbor Wetlands Pirate01 Platform Balista | "The Bloodless" — Ballista | File: scorpion_stationary_marker.ifo | Yes | No |

## MilitaryWall: 8 buildings

| GUID | Size | Internal Name | English Name | IFO Source | BoundingBox | BuildBlocker |
|------|------|---------------|--------------|------------|-------------|-------------|
| 54986 | 0x1 | Military Roman Wall Wood | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 54988 | 0x1 | Military Roman Wall Wood Bridge | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 54997 | 0x1 | Military Roman Celtic Wall Wood | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 54999 | 0x1 | Military Roman Celtic Wall Wood Bridge | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 71448 | 0x1 | Military Roman Celtic Wall Wood Canal Crossing | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 71452 | 0x1 | Military Roman Wall Wood Canal Crossing | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 113960 | 0x1 | Military Roman Celtic Wall Wood Bridge StartEnd | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |
| 114713 | 0x1 | Military Roman Wall Wood Bridge StartEnd | Wooden Palisade | File: roman_wall_wood_10_straight.ifo | Yes | No |

## Module Polygon Field: 4 buildings

| GUID | Size | Internal Name | English Name | IFO Source | BoundingBox | BuildBlocker |
|------|------|---------------|--------------|------------|-------------|-------------|
| 2743 | 1x0 | Module Field Roman Grapes | Vines | File: agriculture_10_field_plant_01.ifo | Yes | No |
| 2744 | 0x0 | Module Field Roman Lavender | Lavender Field | File: basket_01_lavender.ifo | Yes | No |
| 8987 | 0x0 | Module Field Roman Sandarac Wood | Sandarac Grove | File: cypress_tree_02.ifo | Yes | No |
| 23743 | 1x0 | Module Field Roman Celtic Grapes | Vines | File: agriculture_10_field_plant_01.ifo | Yes | No |

## OrnamentalBuilding: 8 buildings

| GUID | Size | Internal Name | English Name | IFO Source | BoundingBox | BuildBlocker |
|------|------|---------------|--------------|------------|-------------|-------------|
| 80619 | 0x0 | Ornament Roman Statue 1x1 01 Community | Community Statue | File: community_statue_01.ifo | Yes | No |
| 87384 | 0x0 | BuildersEdition Ornament 1x1 Town Crier Statue | Town Crier Statue | File: town_crier_statue_01.ifo | Yes | No |
| 88285 | 1x0 | HoF Ornament Roman 1x1 Warrior Statue | Officer Of The Pax | File: colossal_roman_statue_01.ifo | Yes | No |
| 93358 | 0x0 | BuildersEdition Ornament 1x1 Wolf Statue | Capitoline Wolf | File: capitoline_wolf.ifo | Yes | No |
| 95594 | 0x0 | Connect Ornament 1x1 Banner | Ornate Banner | File: flag_reward_02.ifo | Yes | No |
| 95595 | 0x0 | Connect Ornament 1x1 Banner Plus | Three Tribes Banner | File: flag_reward_03.ifo | Yes | No |
| 110125 | 0x0 | Twitch Ornament 1x1 Banner China | 稚嫩的魔法师 | File: flagpole_01.ifo | Yes | No |
| 110127 | 0x0 | Twitch Ornament 1x1 Banner US | Cringer | File: flagpole_02.ifo | Yes | No |
