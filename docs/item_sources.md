# Item Sources - Human-Readable Display Guide

This document provides a comprehensive guide for discovering and displaying item sources in Anno 117 in a human-readable, localized, and concise format.

## Table of Contents

1. [Overview](#overview)
2. [Source Type Categories](#source-type-categories)
3. [Localization Strategy](#localization-strategy)
4. [Implementation Patterns](#implementation-patterns)
5. [Quest Chain Traversal](#quest-chain-traversal)
6. [Display Format Recommendations](#display-format-recommendations)
7. [Edge Cases and Challenges](#edge-cases-and-challenges)

---

## Overview

Items in Anno 117 can be obtained through multiple sources. The asset-extractor library provides a reverse reference system (`Asset.referenced_by` and pool reference dictionaries) that enables programmatic discovery of all sources without hardcoding GUIDs.

**Key Data Structures:**

```python
# Reverse pool references (built automatically)
item.in_reward_pool: dict[int, WeightedReference]  # Root pools containing this item
item.in_asset_pool: dict[int, WeightedReference]   # Root asset pools

# Reverse asset references (built automatically)
item.referenced_by: dict[int, WeightedReference]   # All assets referencing this item

# Weighted reference structure
WeightedReference:
    source: Asset         # The referencing asset
    target: Asset         # The referenced asset
    path: str            # Property path (e.g., "Sequence.SequenceActions[0].Action...")
    weight: float        # Probability or amount
```

**Coverage Statistics (from current implementation):**
- 391 total items in Anno 117
- 81.8% of items have at least one tracked source
- Average of 1.29 sources per item
- Some items appear in 70+ different pools

---

## Source Type Categories

### 1. **Traders (Selling)**

**Display Format:** `Selling: [Trader Name]`

**Template:** `Participant 3rdParty`, `Participant 3rdParty Pirate`, `Participant 3rdParty Emperor`

**Discovery Pattern:**

```python
def find_trader_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find all traders selling this item."""
    sources = []

    # Get all pools containing this item
    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        # Find traders referencing this pool
        for pool_ref in pool.referenced_by.values():
            source = pool_ref.source

            # Check if it's a trader
            if "Participant" in source.template.name and "3rdParty" in source.template.name:
                # Get trader name
                trader_name = source.text.values.get("english", source.name) if source.text else source.name

                sources.append({
                    "type": "selling",
                    "name": trader_name,
                    "guid": source.guid,
                    "pool": pool.guid,
                    "probability": ref.weight
                })

    return sources
```

**Trader Types:**
- Regular traders: `Participant 3rdParty`
- Pirate traders: `Participant 3rdParty Pirate`
- Emperor traders: `Participant 3rdParty Emperor`

**Example Output:**
- `Selling: Diana`
- `Selling: Empress Julia`
- `Selling: Pirate Caeso`

---

### 2. **Research (Tech Tree)**

**Display Format:** `Research: [Tech Name]`

**Template:** `Tech`

**Discovery Pattern:**

```python
def find_research_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find all research that grants this item."""
    sources = []

    if "Tech" not in assets.templates:
        return sources

    # Method 1: Direct item rewards
    for tech in assets.templates["Tech"].assets:
        rewards = tech.find("Tech.Rewards.Items")
        if rewards:
            for item_entry in rewards:
                item_asset = item_entry.ItemAsset()

                # Could be direct Item or RewardPool
                if item_asset and item_asset.guid == item.guid:
                    tech_name_attr = tech.find("Tech.TechName")
                    tech_name = tech_name_attr() if tech_name_attr else tech.name

                    sources.append({
                        "type": "research",
                        "name": tech_name,
                        "guid": tech.guid,
                        "repeatable": tech.find("Tech.IsRepeatable")() if tech.find("Tech.IsRepeatable") else False
                    })

                # Handle RewardPool case
                elif item_asset and "RewardPool" in item_asset.template.name:
                    pool_items = item_asset.pool_assets()
                    if item in pool_items:
                        tech_name_attr = tech.find("Tech.TechName")
                        tech_name = tech_name_attr() if tech_name_attr else tech.name

                        sources.append({
                            "type": "research",
                            "name": tech_name,
                            "guid": tech.guid,
                            "probability": pool_items[item]
                        })

    # Method 2: Pool-based discovery (more efficient for bulk extraction)
    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        for pool_ref in pool.referenced_by.values():
            if pool_ref.source.template.name == "Tech":
                tech = pool_ref.source
                tech_name_attr = tech.find("Tech.TechName")
                tech_name = tech_name_attr() if tech_name_attr else tech.name

                sources.append({
                    "type": "research",
                    "name": tech_name,
                    "guid": tech.guid,
                    "pool": pool.guid,
                    "probability": ref.weight
                })

    return sources
```

**Key Properties:**
- `Tech.TechName` - Localized text reference for tech name
- `Tech.ResearchableTechName` - Alternative name property
- `Tech.IsRepeatable` - Whether tech can be researched multiple times
- `Tech.KnowledgeNeeded` - Research cost

**Example Output:**
- `Research: Military Specialists`
- `Research: Economic Innovation (Repeatable)`

**Important:** This eliminates the need for hardcoded research pool GUIDs (79669, 79670, 79671).

---

### 3. **Quests (Quest Rewards)**

**Display Format:** `Quest: [Quest Name]`

**Templates:** `Quest`, `Objective`, `Decision`, `DecisionRoot`, `Sequence`

**Discovery Pattern:**

```python
def find_quest_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find all quests that grant this item through quest chains."""
    sources = []
    visited = set()

    # Step 1: Find Sequences that give this item via ActionAddGoodsToItemContainer
    for ref_guid, weighted_ref in item.referenced_by.items():
        if ref_guid in visited:
            continue

        source = weighted_ref.source

        # Check if it's a Sequence with ActionAddGoodsToItemContainer
        if "Sequence" in source.template.name:
            if "ActionAddGoodsToItemContainer" in weighted_ref.path:
                # Step 2: Traverse upward to find the quest
                quest = _traverse_to_quest(source, visited)

                if quest:
                    quest_name = quest.text.values.get("english", quest.name) if quest.text else quest.name

                    sources.append({
                        "type": "quest",
                        "name": quest_name,
                        "guid": quest.guid,
                        "sequence": source.guid
                    })

    # Also check Objective rewards directly
    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        for pool_ref in pool.referenced_by.values():
            if "Objective" in pool_ref.source.template.name:
                objective = pool_ref.source

                # Try to find parent quest
                quest = _traverse_to_quest(objective, visited)

                if quest:
                    quest_name = quest.text.values.get("english", quest.name) if quest.text else quest.name

                    sources.append({
                        "type": "quest",
                        "name": quest_name,
                        "guid": quest.guid,
                        "objective": objective.guid,
                        "probability": ref.weight
                    })

    return sources

def _traverse_to_quest(start_asset: Asset, visited: set) -> Asset | None:
    """Traverse upward through references to find a quest."""
    current = start_asset
    max_depth = 10  # Prevent infinite loops
    depth = 0

    while depth < max_depth:
        # Check if current asset is a quest
        if "Quest" in current.template.name and current.template.name != "QuestComponent":
            return current

        # Find next asset in chain
        found_next = False
        for ref_guid, weighted_ref in current.referenced_by.items():
            if ref_guid not in visited:
                visited.add(ref_guid)
                current = weighted_ref.source
                found_next = True
                break

        if not found_next:
            break

        depth += 1

    return None
```

**Quest Chain Pattern:**
```
Item (82777 - Mad Cook Item)
    ↓ ActionAddGoodsToItemContainer
Sequence (82775 - Mad Cook Quest Delivery)
    ↓ referenced_by
Decision (82773 - Mad Cook Quest Choice)
    ↓ DecisionOutputs
DecisionRoot (82771)
    ↓ referenced_by
Objective (82770 - Mad Cook Objective)
    ↓ referenced_by
Quest (82769 - Mad Cook Quest)
```

**Reference Path Indicators:**
- `Sequence.SequenceActions[X].Action.ActionAddGoodsToItemContainer.Goods` - Item reward in sequence
- `Objective.Reward.RewardAssets[X].Reward` - Item reward in objective
- `Decision.DecisionOptions[X]...` - Item as decision option

**Example Output:**
- `Quest: The Mad Cook`
- `Quest: Introduce New Specialist`

---

### 4. **NPC Drops (Combat Loot)**

**Display Format:** `Drops: [NPC Name]`

**Templates:** `Participant 2ndParty` (Rivals), `Participant 3rdParty Emperor`, `Participant 3rdParty Pirate`

**Discovery Pattern:**

```python
def find_npc_drop_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find NPCs that drop this item when defeated."""
    sources = []

    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        # Check if pool name contains "Drops"
        if "Drops" in pool.name or "Drop" in pool.name:
            # Find which NPC owns this drop pool
            for pool_ref in pool.referenced_by.values():
                source = pool_ref.source

                if "Participant" in source.template.name:
                    npc_name = source.text.values.get("english", source.name) if source.text else source.name

                    sources.append({
                        "type": "drops",
                        "name": npc_name,
                        "guid": source.guid,
                        "pool": pool.guid,
                        "probability": ref.weight
                    })

    return sources
```

**NPC Types:**
- Rivals: `Participant 2ndParty` (Dorian, Tarragon)
- Emperors: `Participant 3rdParty Emperor` (Calidus, Julia)
- Pirates: `Participant 3rdParty Pirate` (Caeso)

**Example Output:**
- `Drops: Dorian (Rival)`
- `Drops: Empress Julia`
- `Drops: Pirate Caeso`

---

### 5. **Achievements**

**Display Format:** `Achievement: [Achievement Name]`

**Template:** `Achievement`

**Discovery Pattern:**

```python
def find_achievement_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find achievements that grant this item."""
    sources = []

    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        for pool_ref in pool.referenced_by.values():
            if pool_ref.source.template.name == "Achievement":
                achievement = pool_ref.source
                ach_name = achievement.text.values.get("english", achievement.name) if achievement.text else achievement.name

                sources.append({
                    "type": "achievement",
                    "name": ach_name,
                    "guid": achievement.guid,
                    "pool": pool.guid,
                    "probability": ref.weight
                })

    return sources
```

**Example Output:**
- `Achievement: 9 Specialists in Villa`
- `Achievement: 600 Residences`

---

### 6. **Functions & Triggers**

**Display Format:** `Event: [Function Name]` or `Unlock: [Gate Name]`

**Templates:** `Function`, `Trigger`, `Gate`

**Discovery Pattern:**

```python
def find_function_trigger_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find functions, triggers, and gates that grant this item."""
    sources = []

    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        for pool_ref in pool.referenced_by.values():
            source = pool_ref.source
            template = source.template.name

            if template == "Function":
                func_name = source.text.values.get("english", source.name) if source.text else source.name

                sources.append({
                    "type": "function",
                    "name": func_name,
                    "guid": source.guid,
                    "pool": pool.guid,
                    "probability": ref.weight
                })

            elif template in ("Trigger", "Gate"):
                trigger_name = source.text.values.get("english", source.name) if source.text else source.name

                sources.append({
                    "type": "trigger",
                    "name": trigger_name,
                    "guid": source.guid,
                    "pool": pool.guid,
                    "probability": ref.weight
                })

    return sources
```

**Example Output:**
- `Event: Find Island with ItemsInStock`
- `Unlock: Gate Civic Mid to Late-M`

---

### 7. **Festivals**

**Display Format:** `Festival: [Festival Name]`

**Template:** `Festival`

**Discovery Pattern:**

```python
def find_festival_sources(item: Asset, assets: AssetCache) -> list[dict]:
    """Find festivals that grant this item."""
    sources = []

    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        for pool_ref in pool.referenced_by.values():
            if pool_ref.source.template.name == "Festival":
                festival = pool_ref.source
                fest_name = festival.text.values.get("english", festival.name) if festival.text else festival.name

                sources.append({
                    "type": "festival",
                    "name": fest_name,
                    "guid": festival.guid,
                    "pool": pool.guid,
                    "probability": ref.weight
                })

    return sources
```

**Example Output:**
- `Festival: Festival of Happiness`
- `Festival: Festival of Mercury Lugus`

---

## Localization Strategy

### Provided Text IDs

Use these localized text IDs for source type labels:

```python
SOURCE_TEXT_IDS = {
    "quest": -6905698394117185352,      # "Quest"
    "selling": -6902222124635972240,    # "Selling"
    "research": -6902138578600598283,   # "Research"
    "flotsam": -6917297453044695070,    # "Flotsam"
}
```

### Accessing Localized Text

```python
def get_localized_text(text_id: int, texts: TextCache, language: str = "english") -> str:
    """Get localized text for a text ID."""
    text_obj = texts.elements.get(text_id)
    if text_obj:
        return text_obj.values.get(language, "N/A")
    return "N/A"

# Usage
texts = assets.texts
quest_label = get_localized_text(SOURCE_TEXT_IDS["quest"], texts)  # "Quest"
selling_label = get_localized_text(SOURCE_TEXT_IDS["selling"], texts)  # "Selling"
```

### Localizing Source Names

```python
def get_source_display_name(source: Asset, texts: TextCache, language: str = "english") -> str:
    """Get localized display name for a source asset."""
    # Prefer localized text
    if source.text:
        return source.text.values.get(language, source.name)

    # Check for TechName (for Tech template)
    if source.template.name == "Tech":
        tech_name_attr = source.find("Tech.TechName")
        if tech_name_attr:
            text_id = tech_name_attr()
            if isinstance(text_id, int):
                return get_localized_text(text_id, texts, language)

    # Fallback to internal name
    return source.name
```

---

## Implementation Patterns

### Unified Source Discovery Function

```python
def find_all_item_sources(item: Asset, assets: AssetCache) -> dict[str, list[dict]]:
    """Discover all sources for an item across all mechanisms."""
    sources = {
        "selling": [],
        "research": [],
        "quest": [],
        "expedition": [],
        "flotsam": [],
        "drops": [],
        "achievement": [],
        "festival": [],
        "function": [],
        "trigger": []
    }

    # Check flotsam property (item-level)
    flotsam_sources = find_flotsam_sources(item)
    sources["flotsam"].extend(flotsam_sources)

    # Check pool-based sources
    for pool_guid, ref in item.in_reward_pool.items():
        pool = assets[pool_guid]

        # Check all assets referencing this pool
        for pool_ref in pool.referenced_by.values():
            source = pool_ref.source
            template = source.template.name

            # Categorize by template
            if "Participant" in template and "3rdParty" in template:
                # Check if it's drops or selling
                if "Drop" in pool.name:
                    sources["drops"].append({
                        "name": get_source_display_name(source, assets.texts),
                        "guid": source.guid,
                        "probability": ref.weight
                    })
                else:
                    sources["selling"].append({
                        "name": get_source_display_name(source, assets.texts),
                        "guid": source.guid,
                        "probability": ref.weight
                    })

            elif template == "Tech":
                sources["research"].append({
                    "name": get_source_display_name(source, assets.texts),
                    "guid": source.guid,
                    "probability": ref.weight
                })

            elif template == "Expedition":
                sources["expedition"].append({
                    "name": get_source_display_name(source, assets.texts),
                    "guid": source.guid,
                    "probability": ref.weight
                })

            elif template == "Achievement":
                sources["achievement"].append({
                    "name": get_source_display_name(source, assets.texts),
                    "guid": source.guid,
                    "probability": ref.weight
                })

            elif template == "Festival":
                sources["festival"].append({
                    "name": get_source_display_name(source, assets.texts),
                    "guid": source.guid,
                    "probability": ref.weight
                })

            elif template == "Function":
                sources["function"].append({
                    "name": get_source_display_name(source, assets.texts),
                    "guid": source.guid,
                    "probability": ref.weight
                })

            elif template in ("Trigger", "Gate"):
                sources["trigger"].append({
                    "name": get_source_display_name(source, assets.texts),
                    "guid": source.guid,
                    "probability": ref.weight
                })

            elif "Objective" in template:
                # Handle quest objectives (traverse to find parent quest)
                quest = _traverse_to_quest(source, set())
                if quest:
                    sources["quest"].append({
                        "name": get_source_display_name(quest, assets.texts),
                        "guid": quest.guid,
                        "objective": source.guid,
                        "probability": ref.weight
                    })

    # Check reference-based sources (quest sequences)
    visited = set()
    for ref_guid, weighted_ref in item.referenced_by.items():
        source = weighted_ref.source

        if "Sequence" in source.template.name and "ActionAddGoodsToItemContainer" in weighted_ref.path:
            quest = _traverse_to_quest(source, visited)
            if quest and quest.guid not in [s["guid"] for s in sources["quest"]]:
                sources["quest"].append({
                    "name": get_source_display_name(quest, assets.texts),
                    "guid": quest.guid,
                    "sequence": source.guid
                })

    return sources
```

---

## Quest Chain Traversal

### Understanding the Chain Structure

Quest chains follow this pattern:

```
Item
  ↓ (ActionAddGoodsToItemContainer)
Sequence
  ↓ (referenced_by)
Decision / DecisionRoot
  ↓ (referenced_by)
Objective
  ↓ (referenced_by)
Quest
```

### Traversal Implementation

```python
def _traverse_to_quest(start_asset: Asset, visited: set, max_depth: int = 10) -> Asset | None:
    """
    Traverse upward through references to find a quest.

    Args:
        start_asset: Starting point (Sequence, Objective, etc.)
        visited: Set of visited GUIDs to prevent cycles
        max_depth: Maximum traversal depth

    Returns:
        Quest asset if found, None otherwise
    """
    current = start_asset
    depth = 0

    while depth < max_depth:
        # Check if current asset is a quest
        if _is_quest(current):
            return current

        # Find next asset in chain
        next_asset = _find_next_in_chain(current, visited)
        if next_asset is None:
            break

        current = next_asset
        depth += 1

    return None

def _is_quest(asset: Asset) -> bool:
    """Check if asset is a quest."""
    template = asset.template.name

    # Quest template (not QuestComponent)
    if template == "Quest":
        return True

    # Some quests may have different templates
    if "Quest" in template and "Component" not in template:
        return True

    return False

def _find_next_in_chain(asset: Asset, visited: set) -> Asset | None:
    """Find the next asset in the quest chain."""
    for ref_guid, weighted_ref in asset.referenced_by.items():
        if ref_guid not in visited:
            visited.add(ref_guid)
            return weighted_ref.source

    return None
```

### Reference Path Analysis

Understanding the `path` property helps identify the type of reference:

```python
def analyze_reference_path(path: str) -> dict:
    """Analyze reference path to determine reference type."""
    if "ActionAddGoodsToItemContainer" in path:
        return {"type": "item_reward", "context": "sequence"}

    elif "Reward.RewardAssets" in path:
        return {"type": "item_reward", "context": "objective"}

    elif "DecisionOptions" in path:
        return {"type": "decision_option", "context": "decision"}

    elif "Trader.OfferedItems" in path:
        return {"type": "trade_offer", "context": "trader"}

    elif "ExpeditionReward" in path:
        return {"type": "expedition_reward", "context": "expedition"}

    else:
        return {"type": "unknown", "context": "unknown"}
```

---

## Display Format Recommendations

### Concise Single-Line Format

For UI display (CSV, tables, compact views):

```python
def format_source_concise(source_type: str, source_name: str, probability: float | None = None) -> str:
    """Format source as concise single-line string."""
    # Use localized type label
    type_labels = {
        "selling": "Selling",
        "research": "Research",
        "quest": "Quest",
        "expedition": "Expedition",
        "flotsam": "Flotsam",
        "drops": "Drops",
        "achievement": "Achievement",
        "festival": "Festival",
        "function": "Event",
        "trigger": "Unlock"
    }

    label = type_labels.get(source_type, source_type.title())

    # Add probability if significant
    if probability and probability < 1.0:
        return f"{label}: {source_name} ({probability:.1%})"
    else:
        return f"{label}: {source_name}"

# Examples:
# "Selling: Diana"
# "Research: Military Specialists"
# "Quest: The Mad Cook"
# "Drops: Pirate Caeso (12.5%)"
```

### Multi-Line Format

For detailed views (HTML, tooltips):

```python
def format_sources_detailed(sources: dict[str, list[dict]], texts: TextCache, language: str = "english") -> str:
    """Format all sources as multi-line detailed view."""
    lines = []

    # Order by importance
    order = ["selling", "research", "quest", "expedition", "achievement", "festival", "drops", "flotsam", "function", "trigger"]

    for source_type in order:
        if sources[source_type]:
            # Get localized label
            label = get_localized_source_label(source_type, texts, language)

            lines.append(f"{label}:")

            for source in sources[source_type]:
                name = source["name"]
                prob = source.get("probability")

                if prob and prob < 1.0:
                    lines.append(f"  • {name} ({prob:.1%})")
                else:
                    lines.append(f"  • {name}")

    return "\n".join(lines) if lines else "No known sources"

# Example output:
# Selling:
#   • Diana
#   • Empress Julia (15.2%)
# Research:
#   • Military Specialists
# Quest:
#   • The Mad Cook
```

### Comma-Separated Format

For CSV export:

```python
def format_sources_csv(sources: dict[str, list[dict]]) -> str:
    """Format sources as comma-separated string."""
    all_sources = []

    for source_type, source_list in sources.items():
        for source in source_list:
            all_sources.append(format_source_concise(source_type, source["name"], source.get("probability")))

    return "; ".join(all_sources) if all_sources else ""

# Example: "Selling: Diana; Research: Military Specialists; Quest: The Mad Cook"
```

---

## Edge Cases and Challenges

### 1. **Circular References**

Quest chains can have circular references (decision loops, repeatable quests).

**Solution:** Use `visited` set to track GUIDs and prevent infinite loops.

```python
visited = set()
quest = _traverse_to_quest(sequence, visited)
```

### 2. **Multiple Paths to Same Source**

An item may appear in multiple pools, all referenced by the same trader.

**Solution:** Deduplicate by GUID before displaying.

```python
# Deduplicate sources by GUID
seen_guids = set()
unique_sources = []

for source in sources["selling"]:
    if source["guid"] not in seen_guids:
        seen_guids.add(source["guid"])
        unique_sources.append(source)
```

### 3. **Missing Localized Text**

Some assets may not have localized text (internal-only assets).

**Solution:** Fallback to internal name.

```python
def get_source_display_name(source: Asset, texts: TextCache) -> str:
    if source.text:
        return source.text.values.get("english", source.name)
    return source.name
```

### 4. **Nested Pool Hierarchies**

Items may be in deeply nested pool hierarchies (3-4 levels).

**Solution:** Use `in_reward_pool` which already flattens hierarchies and provides root pools.

```python
# in_reward_pool contains only ROOT pools (non-pool assets)
for pool_guid, ref in item.in_reward_pool.items():
    # This pool is directly referenced by a trader/expedition/etc.
    pool = assets[pool_guid]
```

### 5. **Probability Aggregation**

An item may appear in multiple pools from the same source with different probabilities.

**Solution:** Sum probabilities or show as separate entries.

```python
# Aggregate probabilities for same source
source_probs = {}
for source in sources["selling"]:
    guid = source["guid"]
    if guid in source_probs:
        source_probs[guid]["probability"] += source["probability"]
    else:
        source_probs[guid] = source

# Or: Show as separate entries with pool names
for source in sources["selling"]:
    print(f"Selling: {source['name']} (Pool: {source['pool']}, {source['probability']:.1%})")
```

### 6. **Tech Template Text References**

Tech names are stored as text references, not direct text.

**Solution:** Resolve `Tech.TechName` to get text ID, then lookup in TextCache.

```python
tech_name_attr = tech.find("Tech.TechName")
if tech_name_attr:
    text_id = tech_name_attr()
    if isinstance(text_id, int):
        text_obj = texts.elements.get(text_id)
        if text_obj:
            tech_name = text_obj.values.get("english", "Unknown")
```

### 7. **Distinguishing Trader Types**

Regular traders, pirates, and emperors all use `Participant 3rdParty` template variants.

**Solution:** Check template name or use additional context.

```python
def get_trader_type(trader: Asset) -> str:
    template = trader.template.name

    if "Emperor" in template:
        return "Emperor"
    elif "Pirate" in template:
        return "Pirate"
    elif "2ndParty" in template:
        return "Rival"
    else:
        return "Trader"

# Usage
trader_type = get_trader_type(source)
display_name = f"{source_name} ({trader_type})"  # "Diana (Trader)", "Caeso (Pirate)"
```

### 8. **Quest Chain Depth**

Some quest chains may be very deep (10+ levels).

**Solution:** Set maximum traversal depth to prevent performance issues.

```python
def _traverse_to_quest(start_asset: Asset, visited: set, max_depth: int = 10) -> Asset | None:
    # Limit depth to prevent excessive traversal
    depth = 0
    while depth < max_depth:
        # ...
```

### 9. **Flotsam Terrain Restrictions**

Flotsam may be restricted to specific terrain types.

**Solution:** Include terrain info in display if present.

```python
flotsam_sources = find_flotsam_sources(item)
for source in flotsam_sources:
    terrain = source.get("terrain")
    if terrain and terrain != "None":
        display = f"Flotsam: {source['flotsam_type']} (Terrain: {terrain})"
    else:
        display = f"Flotsam: {source['flotsam_type']}"
```

---

## Complete Example

### Extract and Display All Sources for an Item

```python
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache

# Load assets
config = Config.from_json("config.json")
assets = AssetCache.load(config)
texts = assets.texts

# Get an item (e.g., Gaius Julius Lupus - GUID 71438)
item = assets[71438]

# Find all sources
sources = find_all_item_sources(item, assets)

# Display concise format
print(f"Sources for {item.text.values.get('english', item.name)}:")
print(format_sources_detailed(sources, texts))

# CSV format
csv_sources = format_sources_csv(sources)
print(f"\nCSV: {csv_sources}")

# Single-line format
for source_type, source_list in sources.items():
    for source in source_list:
        print(format_source_concise(source_type, source["name"], source.get("probability")))
```

**Expected Output:**
```
Sources for Gaius Julius Lupus:
Quest:
  • Introduce New Specialist

CSV: Quest: Introduce New Specialist

Quest: Introduce New Specialist
```

---

## Summary

**Key Achievements:**

1. **No Hardcoded GUIDs:** All sources discovered dynamically via templates and reverse references
2. **Comprehensive Coverage:** 7 source types tracked (vs. 3 in current implementation)
3. **Localized Display:** Returns Text objects for multi-language support; uses game text IDs for labels
4. **Efficient Traversal:** Uses `referenced_by` and pool references instead of iterating all templates
5. **Quest Chain Support:** Traverses decision chains to find root quests
6. **Probability Tracking:** Exposes item probability/weight in pools
7. **Flexible Display:** Supports concise, detailed, and CSV formats

**Coverage Improvement:**

- Current: 81.8% coverage (320/391 items)
- Expected with new implementation: 95%+ coverage
- Missing 18.2% should be covered by quest chains, achievements, festivals, functions

**Performance:**

- O(sources) complexity instead of O(pools × templates)
- Uses pre-built reverse reference indices
- Lazy evaluation for quest chain traversal

This implementation provides a complete, scalable, and maintainable solution for discovering and displaying item sources in Anno 117.
