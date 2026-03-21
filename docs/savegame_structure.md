# Anno 1800 / Anno 117 Savegame Structure

This document describes the binary structure of Anno 1800 (`.a7s`) and Anno 117: Pax Romana (`.a8s`) savegame files. Both games use the same container format and a very similar internal structure.

**References:**
- [Anno Designer Anno 117 savegame docs](https://github.com/oliversaggau/anno-designer/blob/Savegames/AnnoDesigner.Import/docs/Anno117_Savegames.md)
- [Anno Union devblog: Roads & Building in the Grid](https://www.anno-union.com/devblog-roads-building-in-the-grid/)

## Container Format

Savegame files (`.a7s` / `.a8s`) are **Resource File V2.2** archives (a Ubisoft Blue Byte proprietary format). They can be extracted using `RDAConsole.exe`.

### Extraction Pipeline

```
.a7s/.a8s file
    |
    v  (RDAConsole.exe extract)
4 inner files (all with .a7s extension, even for Anno 117):
    data.a7s      -- bulk game state (~95% of size)
    gamesetup.a7s -- game configuration
    header.a7s    -- profile, peer data, corporation info
    meta.a7s      -- version and save metadata
    |
    v  (zlib decompress each file)
4 .bin files (raw FileDB binary format)
    |
    v  (SavegameReader.exe or FileDBReader.exe decompress)
4 .xml files (human-readable hex-encoded XML)
```

The final XML files contain all game data. Leaf node values are hex-encoded (little-endian byte order). The parsing code merges all 4 XML trees into a single root `<Content>` element.

### Known Extraction Issues

- **Anno 117**: Some XML tag names start with digits (e.g., `<2ndPriority>`) or contain spaces (e.g., `<AI Time>`, `<AI Rare Tick>`), which are invalid XML. `SavegameReader.exe` skips nodes with spaces; digit-prefixed tags require post-processing (e.g., regex replacement `<2nd` -> `<_2nd`).

## Hex Encoding

All leaf values in the XML are hexadecimal strings representing little-endian binary data. Conversion functions:

| Hex Length | Type | Example Hex | Decoded |
|-----------|------|-------------|---------|
| 2 chars | `uint8` / `bool` | `01` | `True` |
| 4 chars | `int16` | `D003` | `976` |
| 8 chars | `int32` or `float32` | `4DBF0200` | `180045` (int) |
| 8 chars | `float32` | `DB0FC93F` | `1.5707` (float) |
| 16 chars | `int64` | `E666506900000000` | timestamp |
| variable | `utf-16-le` string | `4F006C00640020...` | `"Old World"` |
| variable | `utf-8` string | `6172637469...` | `"arctic_player_kontor"` |

Whether a value is int or float depends on context. The `FileDBReader/FileFormats/a7s_all.xml` file contains conversion rules mapping XPaths to types.

## Overall XML Structure

The merged XML tree has a single root `<Content>` element. The primary data resides under `MetaGameManager`:

```
Content
+-- MetaGameManager
|   +-- GameCount              (int: elapsed game time in ms)
|   +-- GameTotal              (int: total game time * 100)
|   +-- PlayTotal              (int: real play time in ms)
|   +-- CreatingAccountID      (utf-16 string: Ubisoft account UUID)
|   +-- NetworkSafeRandom
|   +-- MetaMessageManager
|   +-- MetaUnlockManager
|   +-- NotificationSystem
|   +-- MetaGameObjectManager
|   +-- ParticipantManager
|   +-- ParticipantUnlockManager
|   +-- ConditionManager
|   +-- QuestManager
|   +-- EconomyManager
|   +-- PopulationManager
|   +-- EconomyStatisticManager
|   +-- WinLoseManager
|   +-- SessionTradeRouteManager
|   +-- UniqueNamingManager
|   +-- DiplomacyManager           (Anno 117 only)
|   +-- ContractManager            (Anno 117 only)
|   +-- MetaReligionManager        (Anno 117 only)
|   +-- GovernorDecisionManager    (Anno 117 only)
|   +-- GameSessions               (array of sessions)
|
+-- CorporationProfile            (from header.a7s)
|   +-- GameSeed
|   +-- PeerData
|   +-- SavegameProfileDisplayName (utf-16: profile name)
|   +-- DifficultyPreset
|   +-- ActiveDLCs
|   +-- Slots
|
+-- GameSetupManager               (from gamesetup.a7s)
|   +-- GameSeed
|   +-- DifficultyPreset
|   +-- Setup* (various difficulty settings)
|
+-- (meta.a7s fields)
    +-- CorporationFileVersion
    +-- CorporationVersionName     (utf-16: game title string)
    +-- CorporationSaveGameName    (utf-16: save slot name)
    +-- LastModTime
```

## GameSessions

Sessions are stored as an interleaved array of `<None>` elements under `MetaGameManager/GameSessions`:

```xml
<GameSessions>
  <None>SESSION_ID_HEX</None>      <!-- int: session identifier -->
  <None>                            <!-- session data object -->
    <SessionDesc>
      <SessionGUID>...</SessionGUID>
    </SessionDesc>
    <SessionData>
      <BinaryData>
        <Content>
          <GameSessionManager>...</GameSessionManager>
        </Content>
      </BinaryData>
    </SessionData>
  </None>
  <!-- next session pair... -->
</GameSessions>
```

### Anno 1800 Sessions

| Session GUID | Name |
|-------------|------|
| 180023 | The Old World |
| 180025 | The New World |
| 180045 | Cape Trelawney |
| 112132 | The Arctic |
| 114714 | Enbesa |
| (varies) | Scenarios (Eden, Seasons of Silver, etc.) |

### Anno 117 Sessions

Anno 117 uses different session GUIDs (e.g., 3245, 6627 observed). The session structure is largely the same as Anno 1800 but includes additional managers:
- `RomanizationManager`
- `SeasonManager`
- `SessionCooldownManager`
- `MemorizeManager`

## GameSessionManager

Each session's `GameSessionManager` contains:

```
GameSessionManager
+-- MapTemplate              (island layout templates with positions/sizes)
+-- AreaInfo                  (array: island metadata - owner, name, economy, trade)
+-- AreaManagers              (dict: AreaManager_{id} -> building/object data per island)
+-- WorldManager
|   +-- StreetMap             (Anno 1800 only at this level)
|       +-- StreetID/val      (byte array: street tile types for entire session map)
|       +-- x, y              (int: map dimensions)
+-- IslandManager             (Anno 117: Island1, Island2, ... named nodes)
+-- SessionUnitManager
+-- ItemSessionManager        (area buff effects)
+-- DiscoveryManager
+-- WeatherManager
+-- LoadingPierManager
+-- IrrigationManager
```

## AreaInfo (Islands)

Islands are stored as interleaved ID/data pairs (same pattern as sessions):

```xml
<AreaInfo>
  <None>ISLAND_ID</None>
  <None>
    <!-- Anno 1800 -->
    <Owner><id>OWNER_ID</id></Owner>
    <CityName>HEX_UTF16_NAME</CityName>
    <CityNameGuid>...</CityNameGuid>
    <AreaEconomy>...</AreaEconomy>
    <PassiveTrade>...</PassiveTrade>

    <!-- Anno 117 (differences) -->
    <OwnerProfile>OWNER_ID</OwnerProfile>    <!-- flattened, no nested id -->
    <Fertility>...</Fertility>                <!-- fertility data stored here -->
    <CityNameGuid>INT64_GUID</CityNameGuid>  <!-- uses 64-bit name GUIDs -->
    <PayedSettlementRights>...</PayedSettlementRights>
    <InvadingLandUnits>...</InvadingLandUnits>
    <InvasionState>...</InvasionState>
  </None>
</AreaInfo>
```

### Owner IDs

In Anno 1800, `Owner/id` values 0-3 represent player-controlled islands (human players); higher values are NPCs/pirates. In Anno 117, `OwnerProfile` is a GUID referencing a Participant object (e.g., 41 = human player).

### Anno 117 Fertility Data

Fertilities are stored as an array of int32 GUIDs directly in AreaInfo:

```xml
<Fertility>
  <None>9E080000</None>    <!-- fertility GUID -->
  <None>D10F0000</None>
  <None>81210000</None>
</Fertility>
```

### Anno 117 Name Resolution

Island and session names use 64-bit `LineId` values that map to localized strings. These are extracted from `assets.xml` where regions define `CityNames` items with `LineId` references, translated via `texts_*.xml` files. Session GUIDs (e.g., 3245 = "Latium", 6627 = "Albion") also use this system.

## AreaManagers (Per-Island Data)

Each island has an `AreaManager_{id}` node containing:

```
AreaManager_{id}
+-- AreaObjectManager
|   +-- GameObject
|       +-- objects            (array of all buildings/objects on this island)
+-- AreaRailwayManager         (Anno 1800 only)
|   +-- RailwayNodeGraph
|       +-- Nodes, HorizontalEdges, VerticalEdges
+-- AreaStreetManager          (Anno 117: graph-based roads)
|   +-- Graph
|       +-- Nodes, Edges
+-- AreaAqueductManager        (Anno 117: graph-based aqueducts)
|   +-- Graph
|       +-- Nodes, Edges
+-- AreaCanalManager           (Anno 117: graph-based canals)
+-- AreaHedgeManager           (Anno 117: graph-based hedges)
+-- AreaWallManager            (Anno 117: graph-based walls)
+-- AreaPolygonObjectManager   (Anno 117: farm fields and grid-based objects)
+-- AreaRandomManager          (Anno 117)
+-- AreaFeedbackManager        (Anno 117)
+-- AreaVegetationManager      (Anno 117)
```

## Building/Object Structure

Each object in `AreaObjectManager/GameObject/objects` has:

### Core Fields (both games)

| Field | Type | Description |
|-------|------|-------------|
| `guid` | int32 | Building type identifier (references game assets) |
| `ID` | int32 (1800) / int64 (117) | Unique object identifier |
| `Position` | 3x float32 | World coordinates (x=NE axis, y=vertical, z=NW axis) |
| `Direction` | float32 | Rotation angle in radians (multiples of pi/2) |
| `Variation` | int32 | Visual variation index |
| `StateBits` | int32 | Building state flags (Anno 1800: presence = blueprint; Anno 117: 0x66 = blueprint) |
| `ObjectFolderID` | int32 | Internal folder grouping |

### Anno 1800 Building Components

Buildings in Anno 1800 are identified by which child nodes they have:

| Component | Identifies | Key Data |
|-----------|-----------|----------|
| `Residence7` | Residence | `ResidentCount` (int) |
| `Factory7` | Factory/Production | `CurrentProductivity` (float) |
| `ModuleOwner` | Farm (complex building) | `BuildingModules` or `BinArray` (module ID list) |
| `BuildingModule` | Module (attached to farm) | `ParentFactoryID` (int: owner building ID) |
| `ItemContainer/SocketContainer` | Guild house / Town hall | `SocketItems` (equipped item GUIDs) |
| `UpgradeList/UpgradeGUIDs` | Any upgradeable building | Packed int32 array of buff GUIDs |
| `Powerplant` or specific GUIDs (114751, 117547, 100780) | Power plant | `CurrentProductivity` |
| `Nameable/VehicleName` | Ship | UTF-16 ship name |
| `MetaPersistent/MetaID` | Ship (for trade routes) | Persistent ID for route assignment |

### Anno 117 Building Components

Anno 117 buildings have a **more modular component architecture** with many more explicit component nodes:

| Component | Description |
|-----------|-------------|
| `Building` | Marks as a building (not a decoration/ship) |
| `Residence7` | Residence (same name as 1800, 930 instances observed) |
| `Factory7` | Production building (245 instances) |
| `ModuleOwner` | Farm with modules (57 instances) |
| `BuildingModule` | Module attached to a farm (41 instances) |
| `Warehouse` | Storage building (47 instances) |
| `LoadingPier` | Harbor pier |
| `Shipyard` | Ship construction |
| `Villa` | Special building type (new in 117) |
| `Monument` | Monument building |
| `PublicService` | Public service building (46 instances) |
| `AqueductConsumer` | Needs aqueduct connection (new in 117) |
| `Romanization` | Romanization level tracking (new in 117) |
| `StreetActivation` | Street connection requirement |
| `IncidentInfectable` | Can be affected by incidents |
| `IncidentResolver` | Resolves incidents (fire station, etc.) |
| `AttributeProvider` | Provides attribute bonuses |
| `Buffable` | Can receive buffs |
| `Threatable` | Can be threatened/attacked |
| `Pausable` | Can be paused |
| `LogisticNode` | Part of logistics network |
| `Maintenance` | Has maintenance cost |
| `Health` | Has health points |
| `TileConnector` | Connects to adjacent tiles |
| `FreeAreaproductivity` | Open-area productivity (farms, etc.) |
| `MilitaryGate` | Military wall gate (new in 117) |
| `MeshGraphEdgeSelection` | Wall/fortification segment (new in 117) |
| `Unit` | Mobile unit / garrison |
| `UnitCamp` | Military camp |

### Ships (Anno 117)

Ships in Anno 117 have these components:
```
Buffable, Direction, FeedbackController, Health, ID,
ItemContainer, Maintenance, Mesh, MetaPersistent,
Nameable, ObjectFolderID, Position, PropertyTradeRouteVehicle,
QuestObject, Selection, Sellable, ShipModuleOwner, Unit, guid
```
New: `ShipModuleOwner` (ship modules/upgrades), `PropertyTradeRouteVehicle`, `Sellable`.

### NPC/AI Participants

Both games store AI participants as objects with:
```
Participant, Diplomacy (optional), StateBits, OwnerProfile,
MilitaryAI, NavalMilitaryAI, LandMilitaryAI,
ConstructionAI (optional), ThirdParty (optional),
Pirate (optional), Trader (optional)
```

## Streets and Infrastructure

### Anno 1800: Flat StreetMap

Streets are stored as a flat byte array at the session level:
```
WorldManager/StreetMap/StreetID/val   (or WorldManager/StreetMap/IDVar)
```
- Dimensions: `StreetMap/x` and `StreetMap/y` (typically 1920x1920)
- Each byte represents a street type ID (0 = no street)
- Street IDs map to types: road, brick road, quay, canal, railway, bridge, etc.
- The array is indexed as `[y * width + x]` and needs transposing + flipping for correct orientation

### Anno 117: Graph-Based Infrastructure

Anno 117 supports [diagonal construction](https://www.anno-union.com/devblog-roads-building-in-the-grid/) by subdividing each grid tile into 4 sub-tiles, enabling 45-degree placement. Instead of a flat tile array, infrastructure (roads, aqueducts, canals, hedges, walls) is stored as **graphs** per island.

Reference: [Anno Designer Anno 117 savegame docs](https://github.com/oliversaggau/anno-designer/blob/Savegames/AnnoDesigner.Import/docs/Anno117_Savegames.md)

Each infrastructure type has its own manager within an `AreaManager`:

```
AreaManager_{id}
+-- AreaStreetManager      (roads)
+-- AreaAqueductManager    (aqueducts)
+-- AreaCanalManager       (canals)
+-- AreaHedgeManager       (hedges)
+-- AreaWallManager        (walls)
```

Each manager contains a `Graph` with `Nodes` and `Edges`:

```xml
<AreaStreetManager>
  <Graph>
    <Nodes>
      <None>DD010000D10D0000</None>   <!-- position: 2x int32 -->
      <None>
        <Node>
          <Flags>00</Flags>
        </Node>
      </None>
    </Nodes>
    <Edges>
      <None>
        <guid>9A4D0000</guid>         <!-- road type asset GUID -->
        <Edge>
          <PosMin>DD010000D10D0000</PosMin>  <!-- start position -->
          <PosMax>F7010000370F0000</PosMax>  <!-- end position -->
        </Edge>
      </None>
    </Edges>
  </Graph>
</AreaStreetManager>
```

**Important**: Graph coordinates are **scaled by 2** and must be divided by 2 to get world-space positions:
```
Node: DD010000D10D0000
  X raw: 477, Y raw: 3537
  Actual position: (238.5, 1768.5)
```

Walls and fortifications also appear as `MeshGraphEdgeSelection` components on building objects, with `Edge` containing `Min`/`Max` node IDs and an `EdgeGuid` for the wall segment type.

## Polygon Objects (Anno 117 Farm Fields)

Farm fields and other area-based structures in Anno 117 are stored in `AreaPolygonObjectManager` as grid-based polygon objects (not as discrete building objects like in Anno 1800).

```xml
<AreaPolygonObjectManager>
  <Polygons>
    <None>00000000</None>              <!-- polygon ID -->
    <None>
      <GUID>7EA10000</GUID>           <!-- asset type -->
      <SubTilesGrid>
        <GridOriginWS>9800000014070000</GridOriginWS>  <!-- world-space origin: 2x int32 -->
        <Grid>
          <grid>
            <x>84000000</x>            <!-- bits per row -->
            <y>2C000000</y>            <!-- number of rows -->
            <bits>000000F0FF0F...</bits> <!-- nibble-encoded tile data -->
          </grid>
        </Grid>
      </SubTilesGrid>
      <ModuleOwner>
        <ObjectID>0100000081210000</ObjectID>  <!-- owning building -->
      </ModuleOwner>
    </None>
  </Polygons>
</AreaPolygonObjectManager>
```

### Sub-Tile Nibble Encoding

Each nibble (4 bits) in the `bits` array represents one tile. Nibbles are extracted in little-endian order (low nibble first, then high nibble from each byte). Each tile is divided into 4 triangular quadrants from its center:

```
     Top (bit 3)
       /\
      /  \
Left/    \Right
(0) \    / (2)
     \  /
      \/
   Bottom (bit 1)
```

| Value | Bits | Shape |
|-------|------|-------|
| `0x0` | `0000` | Empty |
| `0x1` | `0001` | Left triangle only |
| `0x2` | `0010` | Bottom triangle only |
| `0x3` | `0011` | Bottom-Left half (diagonal) |
| `0x6` | `0110` | Bottom-Right half (diagonal) |
| `0x9` | `1001` | Top-Left half (diagonal) |
| `0xC` | `1100` | Top-Right half (diagonal) |
| `0xF` | `1111` | Full square tile |

The `x` value gives bits per row; divide by 4 to get nibbles (tiles) per row. The actual row stride in the nibble array may include padding: `stride = total_nibbles / rows`.

## Trade Routes

Trade routes are stored under:
```
MetaGameManager/SessionTradeRouteManager/RouteMap
```

Each route contains:
- `ID` (int): Route identifier
- `Name` (utf-16): User-assigned name
- `Ships` (packed int64 array): MetaPersistent IDs of assigned ships
- `Stations/None` (array): Each station has:
  - `AreaID` (int): Island identifier
  - `StationID` (int): Station identifier
  - `GoodInfos` (array): Products and amounts to trade

Trade history is stored per-island:
```
AreaInfo/None/PassiveTrade/History/TradeRouteEntries
```

## MapTemplate (Island Positions)

Each session's `MapTemplate/TemplateElement/Element` defines island positions:

```xml
<Element>
  <MapFilePath>HEX_UTF16_PATH</MapFilePath>   <!-- e.g., "moderate_l_01" -->
  <Position>X_INT Y_INT</Position>             <!-- packed int32 pair -->
  <Rotation90>INT</Rotation90>                 <!-- 0-3, quarter turns -->
</Element>
```

The `MapFilePath` stem (e.g., `moderate_l_01`) serves as the island template name and determines the island size via lookup tables. The position defines where the island sits within the session's coordinate space.

Anno 117 `MapTemplate` additionally includes:
- `Size` (2x int32): World size dimensions (e.g., 2192x2192)
- `PlayableArea` (4x int32): Playable bounds within the map
- `FertilityGuids` (packed int32 array): Fertilities available on the island
- `FertilitySetGUID` (int32): Fertility set identifier
- `MineSlotActivation`: Mine slot configuration
- `RandomIslandConfig`: Random island generation settings

## Coordinate System

- **X-axis**: Points north-east
- **Y-axis**: Perpendicular to water surface (vertical)
- **Z-axis**: Points north-west
- Building positions use 3D float coordinates `(x, y, z)` where only `x` and `z` matter for 2D layout
- The visualizer transforms coordinates: `relative_position = island_top_left - building_position[x,z]`
- Street arrays use an inverted/transposed coordinate system requiring `np.transpose` + `np.flip`

## Key Differences: Anno 1800 vs Anno 117

| Feature | Anno 1800 | Anno 117 |
|---------|-----------|----------|
| File extension | `.a7s` | `.a8s` |
| Inner files | 4x `.a7s` | 4x `.a7s` (same!) |
| Object IDs | 32-bit int | 64-bit int |
| Island name GUIDs | 32-bit int | 64-bit int |
| Owner field | `Owner/id` (nested) | `OwnerProfile` (flat) |
| Island fertility | Separate field | `Fertility` node in AreaInfo |
| Building components | Implicit (few child nodes) | Explicit (many component nodes) |
| Street storage | Session-level flat byte array (`WorldManager/StreetMap`) | Per-island graph (`AreaStreetManager/Graph` with Nodes/Edges) |
| Diagonal building | Not supported | Sub-tile grid (4 sub-tiles per tile, 45-degree placement) |
| Farm fields | Discrete `Module` building objects | `AreaPolygonObjectManager` with nibble-encoded sub-tile grids |
| Railway | `AreaRailwayManager` per island | Not observed |
| Aqueducts | N/A | `AreaAqueductManager` (graph) + `AqueductConsumer` component |
| Canals | N/A | `AreaCanalManager` (graph) |
| Hedges | N/A | `AreaHedgeManager` (graph) |
| Walls | N/A | `AreaWallManager` (graph) + `MeshGraphEdgeSelection` on objects |
| Romanization | N/A | `Romanization` component |
| Seasons | N/A | `SeasonManager` |
| Religion | N/A | `MetaReligionManager` |
| Blueprint detection | `StateBits` node present | `StateBits` = 0x66 |
| Graph coordinates | N/A | Scaled by 2 (divide by 2 for world-space) |
| Invalid XML tags | None | Tags starting with digits (e.g., `<2ndPriority>`) |
| AreaManager children | ObjectManager, RailwayManager | ObjectManager, StreetManager, AqueductManager, CanalManager, WallManager, HedgeManager, PolygonObjectManager, etc. |

## Useful XPaths

### Global
- `MetaGameManager/GameCount` - Game time in ms
- `CorporationProfile/GameSetup/GameSeed` (1800) / `CorporationProfile/GameSeed` (117) - Map seed
- `CorporationProfile/GameSetup/SavegameFolderW` (1800) / `CorporationProfile/SavegameProfileDisplayName` (117) - Profile name
- `MetaGameManager/EconomyStatisticManager/History` - Economic statistics

### Per Session
- `GameSessionManager/AreaInfo` - All islands with owner, name, economy
- `GameSessionManager/AreaManagers/AreaManager_{id}/AreaObjectManager/GameObject/objects` - All buildings
- `GameSessionManager/WorldManager/StreetMap` - Street layout (1800 only)
- `GameSessionManager/MapTemplate/TemplateElement/Element` - Island positions and sizes
- `GameSessionManager/ItemSessionManager/AdditionalAreaEffects` - Area buff effects

### Per Island (Anno 117)
- `AreaManager_{id}/AreaStreetManager/Graph` - Road graph (nodes + edges)
- `AreaManager_{id}/AreaAqueductManager/Graph` - Aqueduct graph
- `AreaManager_{id}/AreaPolygonObjectManager/Polygons` - Farm fields (sub-tile grids)

### Per Building
- `guid` - Building type
- `Position` - 3D coordinates
- `Direction` - Rotation (radians)
- `Residence7/ResidentCount` - Population count
- `Factory7/CurrentProductivity` or `Powerplant/CurrentProductivity` - Productivity
- `ModuleOwner/BinArray` (GU16+) or `ModuleOwner/BuildingModules` (pre-GU16) - Farm modules
- `BuildingModule/ParentFactoryID` - Module's parent building
- `UpgradeList/UpgradeGUIDs` - Applied buff GUIDs
- `ItemContainer/SocketContainer/SocketItems/None/GUID` - Equipped items (town halls, trade unions)
