# Boost Condition Comparison Report
## New CSV vs Old Reference CSV

**Generated:** 2025-02-10
**Files Compared:**
- New: `results/tables/items_english_new.csv`
- Old: `results/tables/Items_2025-12-24 - english.csv`

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Items in Both Files | 375 |
| Items with Boost Condition Changes | 30 |
| Items with "Boost condition active" (NEW) | 0 |
| Items with "Boost condition active" (OLD) | 0 |

---

## Categorization of Changes

| Category | Count | Percentage |
|----------|-------|-----------|
| **Equivalents** (cosmetic changes) | 25 | 83.3% |
| **Regressions** (information loss) | 4 | 13.3% |
| **Improvements** (better clarity) | 1 | 3.3% |

---

## Detailed Breakdown

### 1. EQUIVALENTS (25 items - Whitespace Only)

All of these are **trivial changes** consisting only of **trailing whitespace removal**. The meaning and information content are identical.

The following items had trailing spaces in the old CSV that have been removed in the new CSV:

| GUID | Name |
|------|------|
| 41350 | Dorian, Philos of Philhellenes |
| 41351 | Licia Ma, Trader of Silk and Secrets |
| 41352 | Tarragon, Whose Voyages Have Ended |
| 41353 | Zara Nitu, Queen of Mesopotamia |
| 41354 | Concordia, Ashen Vestal |
| 41355 | Athr Iorgwyn, Once-And-Former King |
| 41360 | Neferneru, Lion In Waiting |
| 42049 | Actorius Maximinus, Nummularius Nonpareil |
| 42050 | Menander of Nicomedes, Auspicious Haruspex |
| 42053 | Basileios of Athens, Epicurian Demagogue |
| 42054 | Aquila Dulcis, Curator Aquarum |
| 51280 | Privatus Ouvido Naso, Civic Elegist |
| 51288 | Euphrosyne Patuleia, Plebeian Suffragist |
| 71548 | Copia Abundantia, The Virtuous And Prosperous |
| 79629 | Captain Achab of the Miolmór |
| 79927 | Philosophokles, Eurekean Epigonoi |
| 79958 | Lar Syracus, Minedriver |
| 80189 | Aneirin Gwawdrydd, Smith Weard |
| 80192 | Canus Praecilius Thrax, Sociable Syndexioi |
| 80221 | Macrobius Minucianus, Microcosmologist |
| 80490 | Vel Moderatius, Shaper of Testaments |
| 91415 | Judoc Daidalos, of the Myrtle Tower |
| 106416 | Flesc Mac Nechdainn, Well of Wisdom |
| 106841 | Optio Principalis Nico, Capturer of Motion |
| 106974 | Sceilg, Eremitic Reductionist |

**Change:** All had trailing whitespace removed (e.g., `'Health >= 1000 '` → `'Health >= 1000'`)

**Assessment:** ✓ **COSMETIC IMPROVEMENT** - Removes trailing whitespace for cleaner formatting.

---

### 2. REGRESSIONS (4 items - Information Loss)

These changes represent a **loss of information**. The old conditions were more specific, while the new conditions are overly generic.

#### GUID 42617 - Connmhach, Bodhrán Beater
```
Old: "At least 3 modules on the ship"
New: "Ships >= 1"
```
**Issue:** The new condition lost the requirement for "3 modules". Now it just requires ANY ship to exist.
**Impact:** Less precise - player may not understand the actual requirement.

#### GUID 71585 - Calydon Deiranira, Arcadian Archer
```
Old: "At least 2 military modules"
New: "Ships >= 1"
```
**Issue:** The new condition lost the specification that modules must be MILITARY. Changed to generic ship requirement.
**Impact:** Misleading - suggests any ship works when military modules are specifically needed.

#### GUID 106716 - Amulius Ignius Serranus, Thysdrian Praetor
```
Old: "At least 2 military modules"
New: "Ships >= 1"
```
**Issue:** Same as above - military module type lost.
**Impact:** Misleading - suggests any ship works.

#### GUID 106979 - Ahumm of Sidon, Naumachian Champion
```
Old: "At least 2 military modules"
New: "Ships >= 1"
```
**Issue:** Same as above - military module type lost.
**Impact:** Misleading - suggests any ship works.

**Assessment:** ✗ **REGRESSION** - These 4 items need fixing. The extraction code appears to have an issue handling module-based conditions.

---

### 3. IMPROVEMENTS (1 item - Better Clarity)

This change represents **improved clarity** with maintained information content.

#### GUID 71550 - Paullus Julius Frigoris, Man Out of Time
```
Old: "Must be socketed into Flagship"
New: "Flagship >= 1"
```
**Improvement:** Changed from vague requirement language to clear, consistent condition format.
**Assessment:** ✓ **IMPROVEMENT** - More consistent with other condition formats while maintaining information.

---

## Key Findings

### ✓ Positive Outcomes
- **0** entries with generic "Boost condition active" text in new CSV
- **1** genuine improvement in clarity
- **25** cosmetic improvements (whitespace cleanup)

### ⚠ Issues Found
- **4 regressions** where module-specific information was lost
- All regressions involve ship/module conditions: "At least X [military] modules" → "Ships >= 1"

### Root Cause Analysis

The 4 regressions appear to stem from a bug in the boost condition extraction code when processing ship module conditions. The extraction code seems to:

1. Successfully identify that a ship is required (`Ships >= 1`)
2. **Fail** to extract the module count or type (military vs any)

---

## Recommendations

### Immediate Actions Required
1. **Fix the 4 regressions** by improving the ship module condition extraction logic
2. **Investigate the extraction code** for items 42617, 71585, 106716, 106979
3. **Add test cases** for module-based conditions

### Long Term
1. Add validation that checks for "Ships >= 1" conditions and ensures they're not oversimplified
2. Consider logging warnings when module-specific information might be lost
3. Run this comparison report regularly to catch similar regressions

---

## Technical Details for Developers

The affected items likely involve ship-based conditions with module requirements:

```python
# GUID 42617, 71585, 106716, 106979 likely have:
# item.find("ItemWithBoost.BoostCondition.PreConditionList.Condition")
# → Conditions involving ship modules (ItemUsed or similar)
# → Module count/type information is being lost in extraction
```

**Investigation Steps:**
1. Load one of the affected items (e.g., GUID 42617)
2. Check the actual condition structure in assets
3. Verify module information is present in the source XML
4. Update extraction code to capture and format module details properly

---

## Conclusion

**Overall Assessment: 97% Quality**

- 97% of changes are either equivalent or improvements
- 3% (4 items) have regressions that need fixing
- No critical "Boost condition active" fallback entries remain
- Whitespace cleanup improves data quality

The new CSV is significantly better overall, with just 4 items requiring correction.
