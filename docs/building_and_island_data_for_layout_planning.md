# Building and Island Data for Layout Planning

Reference for city optimizer / layout planner tools. Documents where each data type lives in this repo and what still needs to be extracted.

## Building Data

### Sizes (width x height footprint)

- **Script**: `assetextractor/conversion/calculator/building-sizes.py`
- **Output**: `results/planner/building-sizes.json` — maps building GUIDs to `[width, height]`
- **Source geometry**: `.cache/data/base/graphics/**/*.ifo` (extracted from `graphics_*.rda`)
- **Run**: `uv run python -m assetextractor.conversion.calculator.building-sizes`

IFO path resolution uses a 5-level priority (see `get_building_ifo_path()`, L308-392):
1. `Object.Variations[0].Filename` (L326-336) — standard buildings
2. `MeshGraphStyle.AdditionalConfigs[0].ConfigFile` (L338-350) — gates, hedges
3. `Wall.TileSetCfgFolder` / `Aqueduct.TileSetCfgFolder` (L352-361) — modular structures
4. `MeshGraphEdgeSelection.HitBoxReferenceCfg` (L363-371) — reference buildings
5. `Polygon.Path` glob (L373-392) — fallback

Size extraction strategies per IFO (see `get_building_size_from_ifo()`, L153-237):
1. `BuildBlocker/Position` corners (L174-207) — most accurate
2. `BoundingBox/Extents` xf/zf (L209-225)
3. Filename pattern e.g. `04x04` (L227-231)
4. Asset name pattern e.g. `Ornament 1x1` (L437-443)

### Cycle Times, Inputs, Outputs, Maintenance

- **Notebook**: `assetextractor/conversion/calculator/conversion_calculator.ipynb`, cell 32 (`2ab1c7ce`)
- **Output key**: `factories` in `../anno-117-calculator/js/params.js`
- **Fields extracted per factory**:
  - `cycleTime` from `FactoryBase.CycleTime`
  - `inputs` from `FactoryBase.FactoryInputs` (product GUID + amount)
  - `outputs` from `FactoryBase.FactoryOutputs` (product GUID + amount)
  - `maintenances` from `Maintenance.Maintenances`
  - `modulesLimit` from `ModuleOwner.ModuleLimits.Main.Limit`
  - `buffs` from `Building.FunctionalEffects`
- Iterates `templates.groups["Objects"]["Buildings"]["Factories"]`

### Building Buffs (Workforce Modifiers)

- **Notebook**: `assetextractor/conversion/calculator/conversion_calculator.ipynb`, cell 36 (`j8ksopc0dwe`)
- **Output key**: `buildingBuffs` in `params.js`
- **Workforce-relevant fields**:
  - `workforceModifierInPercent` from `BuildingUpgrade.WorkforceModifierInPercent`
  - `additionalWorkforces` from `BuildingUpgrade.AdditionalWorkforces`
  - `workforceMaintenanceFactorUpgrade` from `MaintenanceUpgrade.WorkforceMaintenanceFactorUpgrade`
  - `replaceWorkforce` from `MaintenanceUpgrade.ReplaceWorkforce`

---

## Population Data

All extracted in `assetextractor/conversion/calculator/conversion_calculator.ipynb`, output to `../anno-117-calculator/js/params.js`.

### Workforce Products

- **Cell**: 27 (`f45bb1c8`)
- **Output key**: `workforce`
- Filters `templates["Product"].assets` by `Product.IsWorkforce()`
- Includes `associatedRegions` per workforce type (Liberti, Plebeian, Equites, Patrician, etc.)

### Population Levels (Workforce Conversion Factor)

- **Cell**: 25 (`11cfb960`)
- **Output key**: `populationLevels`
- **Fields**:
  - `connectedWorkforce` — GUID of the workforce product this level generates
  - `populationToWorkforceFactor` from `PopulationLevel.PopulationToWorkforceFactor`
  - `associatedRegions` — derived from residence building data

### Population Groups

- **Cell**: 22 (`8222d585`)
- **Output key**: `populationGroups`
- `PopulationGroup7.PopulationLevels` — list of level GUIDs per group
- `PopulationGroup7.Regional` — associated region

### Residence Buildings (Needs per Tier)

- **Cell**: 23 (`e2089bfe`)
- **Output key**: `residenceBuildings`
- **Fields**:
  - `populationLevel` from `Residence7.PopulationLevel`
  - `needsList` from `Residence7.NeedsList` — list of `{ need, needConsumptionRate }`
  - `possibleUpgrades` from `Upgradable.PossibleUpgrades`
  - `associatedRegions` from `Building.AssociatedRegions`

---

## Island Data

### Island Positions and Template Names (from Savegame)

Island layout in a running game comes from the savegame (`.a8s`), not from `assets.xml`. See `docs/savegame_structure.md` for the full binary format.

**XPath**: `GameSessionManager/MapTemplate/TemplateElement/Element` (savegame_structure.md L476-494)

Each element contains:
- `MapFilePath` — UTF-16 hex string, stem is the island template name (e.g. `moderate_l_01`, `latium_extralarge_01`)
- `Position` — packed int32 pair: island origin in session world-space
- `Rotation90` — 0-3, quarter-turn rotations
- `Size` — 2x int32 world dimensions (Anno 117 only)
- `PlayableArea` — 4x int32 playable bounds (Anno 117 only)
- `FertilityGuids` — packed int32 array of fertilities on this island
- `MineSlotActivation` — mine/resource slot configuration

The `MapFilePath` stem determines island size via lookup. The inline dict in `extract_params_for_tools.ipynb` maps these stems to `[width, height]`.

### Building Positions on Islands (from Savegame)

**XPath**: `GameSessionManager/AreaManagers/AreaManager_{id}/AreaObjectManager/GameObject/objects` (savegame_structure.md L222-224)

Per building object (savegame_structure.md L247-257):
- `guid` — building type (cross-reference with `params.js` factory/residence GUIDs)
- `Position` — 3x float32 world coordinates; only x and z matter for 2D layout
- `Direction` — float32 rotation in radians (multiples of pi/2)
- `Variation` — visual variation index
- `StateBits` = `0x66` means blueprint (not yet built)

Coordinate transform: `relative_pos = island_top_left - building_position[x, z]` (savegame_structure.md L502)

### Farm Fields (from Savegame)

Farm fields are not discrete building objects. They are stored as sub-tile polygon grids (savegame_structure.md L397-451):

**XPath**: `AreaManager_{id}/AreaPolygonObjectManager/Polygons`

Each polygon has:
- `GUID` — asset type
- `SubTilesGrid/GridOriginWS` — 2x int32 world-space origin
- `SubTilesGrid/Grid/grid/bits` — nibble-encoded tile data (4 bits per sub-tile)
- `ModuleOwner/ObjectID` — owning factory building ID

Nibble extraction (low nibble first per byte):
```csharp
yield return (byte)(b & 0x0F); // low nibble first
yield return (byte)(b >> 4);   // then high nibble
```

Column count = `x / 4` (x is bits per row). Row stride = `bits.Length / rows` (may include padding). Tile center = `(col + originX + 0.5, row + originY + 0.5)`.

All 16 nibble values (each tile is 4 triangular quadrants: bit0=Left, bit1=Bottom, bit2=Right, bit3=Top):

| Value | Shape |
|---|---|
| `0x0` | Empty |
| `0x1` | Left triangle only |
| `0x2` | Bottom triangle only |
| `0x4` | Right triangle only |
| `0x8` | Top triangle only |
| `0x3` | Bottom-Left diagonal half |
| `0x6` | Bottom-Right diagonal half |
| `0x9` | Top-Left diagonal half |
| `0xC` | Top-Right diagonal half |
| `0x7` | Full minus Top |
| `0xB` | Full minus Right |
| `0xD` | Full minus Bottom |
| `0xE` | Full minus Left |
| `0xF` | Full square tile |

### Roads, Aqueducts, Walls (from Savegame)

All infrastructure in Anno 117 is stored as graphs per island (savegame_structure.md L345-395):

| Manager | Content |
|---|---|
| `AreaStreetManager/Graph` | Roads |
| `AreaAqueductManager/Graph` | Aqueducts |
| `AreaCanalManager/Graph` | Canals |
| `AreaHedgeManager/Graph` | Hedges |
| `AreaWallManager/Graph` | Walls |

Each graph has `Nodes` (position as 2x int32) and `Edges` (PosMin/PosMax + road type GUID). **Graph coordinates are scaled by 2** — divide by 2 for world-space position.

### Island Outline / Tile Shape

Island outlines are **not stored in the savegame**. The savegame only stores the `MapFilePath` (e.g. `data/base/provinces/latium_extralarge_01.a7m`) which references the island template file. The actual per-tile shape of the island — including coastline, forest areas, meadow areas, river slots, and mountain slots — is encoded in the `.a7m` / `.a7minfo` files distributed with the game.

AnnoDesigner currently handles this by **hardcoding island sizes** (width × height bounding box) derived from `.a7minfo` files. It does not decode per-tile outlines.

To get full tile-level island outlines for a layout planner, the `.a7m` or `.a7minfo` files would need to be extracted from the map RDAs and parsed. The current `assetextractor/extraction/extract.py` does not cover this — it only extracts building `.ifo` files from `graphics_*.rda`.

---

## Key Output Files Summary

| Data | Source | File / Location |
|---|---|---|
| Building sizes (w x h) | `assets.xml` + `.ifo` files | `results/planner/building-sizes.json` |
| Factory cycle times, I/O, maintenance | `assets.xml` | `../anno-117-calculator/js/params.js` — `factories` |
| Workforce products | `assets.xml` | `../anno-117-calculator/js/params.js` — `workforce` |
| Population levels + workforce factor | `assets.xml` | `../anno-117-calculator/js/params.js` — `populationLevels` |
| Population groups | `assets.xml` | `../anno-117-calculator/js/params.js` — `populationGroups` |
| Residence needs per tier | `assets.xml` | `../anno-117-calculator/js/params.js` — `residenceBuildings` |
| Population needs | `assets.xml` | `results/tables/needs-117-v1.2.csv` |
| Products | `assets.xml` | `results/tables/products-117-v1.2.csv` |
| Island template names + dimensions | `.a7minfo` / savegame | `extract_params_for_tools.ipynb` (inline dict) |
| Island positions + fertilities + mine slots | Savegame `.a8s` | `MapTemplate/TemplateElement/Element` — see `docs/savegame_structure.md` L476 |
| Building positions per island | Savegame `.a8s` | `AreaManager_{id}/AreaObjectManager` — see `docs/savegame_structure.md` L222 |
| Farm field shapes | Savegame `.a8s` | `AreaPolygonObjectManager/Polygons` — see `docs/savegame_structure.md` L397 |
| Road / aqueduct / wall graphs | Savegame `.a8s` | `AreaStreetManager` etc. — see `docs/savegame_structure.md` L345 |
| Island terrain slot geometry | `.a7m` / `.a7minfo` map files | **Not extracted** — must parse map RDAs |

## Reference

- `docs/savegame_structure.md` — full binary format for `.a8s` savegames
- [Anno Designer Anno 117 savegame docs](https://github.com/oliversaggau/anno-designer/blob/Savegames/AnnoDesigner.Import/docs/Anno117_Savegames.md) — C# parsing code for `ProcessTilesGrid`, graph edges, position decoding
