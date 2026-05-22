from dataclasses import asdict, dataclass
from typing import Dict, TypedDict

from assetextractor.parsing.core.assets import Asset
from assetextractor.parsing.core.attributes import DictAttribute


class UpgradeAttributeJSON(TypedDict):
    key: str  # e.g., "maintenance_factor_upgrade", "offense_melee_upgrade"
    label: str  # e.g., "Maintenance Factor", "Melee Offense"
    value: str  # e.g., "-15%", "+20"
    raw: float  # e.g., -0.15, 20.0

@dataclass(frozen=True)
class AdditionalAttributesInfo:
    """The raw numeric attribute values (typically floats/ints)."""

    population: float
    money: float
    happiness: float
    health: float
    fire_safety: float
    belief: float
    knowledge: float
    prestige: float


@dataclass(frozen=True)
class FormattedAttributesInfo:
    """The localized and formatted string values (e.g., '+50', '+25%', '-10')."""

    population: str
    money: str
    happiness: str
    health: str
    fire_safety: str
    belief: str
    knowledge: str
    prestige: str


class AssetWithUpgradeBase(Asset):
    """Common base class providing shared extraction and formatting utilities for upgrades."""

    def _get_val_and_percent(
        self,
        raw_attributes_dict: Dict[str, DictAttribute | None],
        attr_key: str,
        value_keys: tuple[str, ...] = ("AmountOrPercent", "ValueOrPercent"),
    ) -> tuple[float, bool]:
        """Safely extracts raw float values and automatically detects if they represent percentages."""
        attr = raw_attributes_dict.get(attr_key)
        val = 0.0
        is_percent = False

        if attr is not None:
            # Look up the first matching value key inside the DictAttribute (e.g. AmountOrPercent or ValueOrPercent)
            value_attr = None
            for key in value_keys:
                value_attr = attr.find(key)
                if value_attr is not None:
                    break

            if value_attr is not None:
                raw_val = value_attr()
                if raw_val is not None:
                    val = float(raw_val)

                # Inspect string representation from the parser
                attr_str = str(value_attr)

                if "%" in attr_str:
                    is_percent = True

        return val, is_percent

    def _format_attribute(self, val: float, is_percent: bool) -> str:
        """Formats the parsed numeric attribute using the UI text cache mappings."""
        if val == 0.0:
            return "0"

        # Resolve formatting mappings from the active UI Text Cache
        ui_mappings = self.cache.properties.ui_text_cache

        if ui_mappings:
            # Pass the explicit percental parameter to avoid incorrect auto-detection
            return str(ui_mappings._format_value(val, percental=is_percent))

        # Fallback formatting if UITextCache is not yet loaded in context
        if is_percent:
            percent = val * 100 if -1 < val < 1 and val != 0 else val
            if percent == int(percent):
                percent_int = int(percent)
                return f"+{percent_int}%" if percent_int > 0 else f"{percent_int}%"
            return f"+{percent:.1f}%" if percent > 0 else f"{percent:.1f}%"
        else:
            if val == int(val):
                val_int = int(val)
                return f"+{val_int}" if val_int > 0 else str(val_int)
            return f"+{val:.1f}" if val > 0 else f"{val:.1f}"

    def _print_upgrade_info_base(
        self,
        raw: AdditionalAttributesInfo,
        fmt: FormattedAttributesInfo,
        title_prefix: str,
        width: int = 100,
        indent: str = "",
    ) -> None:
        """Unified internal printer shared across building and residence upgrade types."""
        # Fast exit: check if all numeric attributes are exactly zero using asdict and all()
        if all(val == 0.0 for val in asdict(raw).values()):
            return

        # Bundle everything into visual entries for cleaner filtering
        attributes_list = [
            ("Population", raw.population, fmt.population),
            ("Money", raw.money, fmt.money),
            ("Happiness", raw.happiness, fmt.happiness),
            ("Health", raw.health, fmt.health),
            ("Fire Safety", raw.fire_safety, fmt.fire_safety),
            ("Belief", raw.belief, fmt.belief),
            ("Knowledge", raw.knowledge, fmt.knowledge),
            ("Prestige", raw.prestige, fmt.prestige),
        ]

        # Filter out inactive properties
        active_entries = [entry for entry in attributes_list if entry[1] != 0.0]

        if not active_entries:
            return

        if indent:
            # We are rendering nested within an active tree hierarchy
            # Print a neat sub-header block connected directly to the parent tree line
            print(f"{indent}├── [{title_prefix} Attributes]:")
            sub_indent = indent + "│   "
            for i, (name, raw_val, fmt_val) in enumerate(active_entries):
                is_last_item = i == len(active_entries) - 1
                connector = "└── " if is_last_item else "├── "
                print(f"{sub_indent}{connector}{f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})")
        else:
            # Standalone layout format utilizing clean, double-lined box drawing characters
            border = "═" * width
            print(f"╔{border}╗")
            print(f"║ {title_prefix} Attributes (GUID: {self.guid})".ljust(width + 1) + "║")
            print(f"╠{border}╣")
            for name, raw_val, fmt_val in active_entries:
                print(f"║  |- {f'[{name}]:':<15} {fmt_val:<10} (Raw: {raw_val})".ljust(width + 1) + "║")
            print(f"╚{border}╝")
