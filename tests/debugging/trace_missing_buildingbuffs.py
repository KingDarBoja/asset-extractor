"""Trace the 3 remaining untagged buildingBuffs to find their DLC connection."""
from assetextractor.extraction.utils import Config
from assetextractor.parsing.core.assets import AssetCache
from assetextractor.parsing.core.attributes import ReferenceAttribute, ListAttribute, FileNameAttribute

config = Config.from_json("config.json")
assets = AssetCache.load(config)
templates = assets.templates

TARGETS = {153818, 148428, 155091}

def try_name(a):
    if a is None:
        return "???"
    try:
        t = a.text
        if t:
            v = t.values.get("english")
            if v:
                return v
    except Exception:
        pass
    return a.name or str(a.guid)


for guid in TARGETS:
    a = assets.elements.get(guid)
    if a is None:
        print(f"\n{guid}: NOT FOUND")
        continue
    tmpl = a.template.name if a.template else "?"
    print(f"\n=== {guid} [{tmpl}] '{a.name}' ===")

    # Check Standard.IconFilename
    try:
        icon = a.find("Standard.IconFilename")
        if isinstance(icon, FileNameAttribute):
            print(f"  icon: {icon.value}")
    except Exception:
        pass

    # Check who references this as a buff (Effect.Buffs)
    print("  Referenced by Effects via Effect.Buffs:")
    for e in list(assets.elements.values()):
        if e.template and e.template.name == "Effect":
            try:
                for bi in e.Effect.Buffs:
                    ref = bi.GUID
                    if isinstance(ref, ReferenceAttribute) and ref.value and ref.value.guid == guid:
                        print(f"    Effect {e.guid} '{e.name}'")
            except Exception:
                pass

    # Check who references this in inline Effect.Buffs (Items)
    print("  Referenced by Items via inline Effect.Buffs:")
    for tmpl_name in ("Item", "ItemWithBoost"):
        tmpl = templates[tmpl_name]
        if not tmpl:
            continue
        for item in list(tmpl.assets):
            try:
                for bi in item.Effect.Buffs:
                    ref = bi.GUID
                    if isinstance(ref, ReferenceAttribute) and ref.value and ref.value.guid == guid:
                        print(f"    Item {item.guid} '{item.name}' (icon: {item.find('Standard.IconFilename')})")
            except Exception:
                pass

    # For 155091: check parent item 155088
    if guid == 155091:
        parent = assets.elements.get(155088)
        if parent:
            print(f"  Parent 155088: name={parent.name!r}")
            try:
                icon = parent.find("Standard.IconFilename")
                print(f"    icon: {icon.value if isinstance(icon, FileNameAttribute) else icon}")
            except Exception:
                pass

    # For 153818: scan AdditionalFunctionalEffect references
    if guid == 153818:
        print("  Assets referencing 153818 via AdditionalFunctionalEffect:")
        for e in list(assets.elements.values()):
            try:
                afe = e.find("BuildingUpgrade.AdditionalFunctionalEffect")
                if afe and hasattr(afe, "value") and afe.value and afe.value.guid == guid:
                    print(f"    {e.guid} [{e.template.name if e.template else '?'}] '{e.name}'")
            except Exception:
                pass

    # For 148428: check Effect 148427
    if guid == 148428:
        eff = assets.elements.get(148427)
        if eff:
            print(f"  Effect 148427: name={eff.name!r}")
            try:
                icon = eff.find("Standard.IconFilename")
                print(f"    icon: {icon.value if isinstance(icon, FileNameAttribute) else icon}")
            except Exception:
                pass
            # Who references Effect 148427 as FunctionalEffect?
            print("  Buildings with FunctionalEffect 148427:")
            for b in list(assets.elements.values()):
                fe = b.find("Building.FunctionalEffects")
                if fe and isinstance(fe, ListAttribute):
                    for ei in fe:
                        try:
                            fr = ei.FunctionalEffect
                            if isinstance(fr, ReferenceAttribute) and fr.value and fr.value.guid == 148427:
                                print(f"    {b.guid} [{b.template.name if b.template else '?'}] '{b.name}'")
                        except Exception:
                            pass
            # Who references Effect 148427 as a Tech.Rewards.Effect?
            print("  Techs with Rewards.Effects 148427:")
            tech_tmpl = templates["Tech"]
            if tech_tmpl:
                for t in list(tech_tmpl.assets):
                    try:
                        for ei in t.Tech.Rewards.Effects:
                            ref = ei.EffectAsset
                            if isinstance(ref, ReferenceAttribute) and ref.value and ref.value.guid == 148427:
                                print(f"    Tech {t.guid} '{t.name}'")
                    except Exception:
                        pass
