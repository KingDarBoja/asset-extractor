"""UI Text Cache for mapping dataset values to localized text and icons.

This module provides automatic association of UI text to buff attributes by loading
configuration assets that map dataset/enum values to text IDs and icon GUIDs.
"""

from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass, field

from assetextractor.parsing.core.attributes import (
    Attribute,
    DictAttribute,
    FileNameAttribute,
    FlagsAttribute,
    ListAttribute,
    ListItem,
    ReferenceAttribute,
    TextAttribute,
)

if t.TYPE_CHECKING:
    from assetextractor.parsing.core.assets import Asset, AssetCache
    from assetextractor.parsing.core.common import NamedElement
    from assetextractor.parsing.core.texts import Text

logger = logging.getLogger("parsing.uitext")


@dataclass
class UITextMapping:
    """Stores UI text and icon for a dataset value.

    Attributes:
        text_id: The localized text ID (negative number referencing texts_*.xml)
        text: The Text object (for direct access to localized strings)
        icon: The FileNameAttribute for the icon (path to icon file)
        variants: Optional dictionary of variant text IDs for context-specific display
                  (e.g., BuffConstructionCost has ShipyardText, RecruitmentText, etc.)
    """

    text_id: int | None = None
    text: Text | None = None
    icon: FileNameAttribute | None = None
    variants: dict[str, int] = field(default_factory=dict)


@dataclass
class BuffUI:
    """UI representation of a buff attribute with icon, text, and formatted value.

    Attributes:
        icon: The FileNameAttribute for the icon (path to icon file)
        text: The Text object with formatted placeholders (for localized display)
        value: Formatted string representation of the buff value (e.g., "+25%", "50")
        literal: Optional dataset literal (for DictAttribute entries)
    """

    icon: FileNameAttribute | None = None
    text: Text | str | None = None
    value: str | None = ""
    literal: str | None = None

    @property
    def percental(self) -> bool:
        if self.value is not None:
            return self.value.endswith("%")

        return False

    def __str__(self) -> str:
        """String representation using icon filename stem, text, and value."""
        icon_name = ""
        if self.icon and hasattr(self.icon, "value") and self.icon.value:
            icon_name = self.icon.value.stem

        text_str = ""
        if isinstance(self.text, str):
            text_str = self.text
        elif self.text and hasattr(self.text, "values"):
            # Get English text as default
            text_str = self.text()

        parts = [p for p in [icon_name, text_str, self.value] if p]
        return " | ".join(parts)

    def __repr__(self) -> str:
        return self.__str__()


class UITextCache:
    """Centralized cache for UI text mappings from configuration assets.

    This cache loads specific configuration assets that define how dataset/enum values
    should be displayed in the UI. It builds lookup tables mapping (dataset_name, literal)
    pairs to UITextMapping objects containing text IDs and icon GUIDs.

    The configuration is data-driven - you only need to specify which assets to load
    and the path templates for accessing the mappings within those assets.
    """

    # Configuration: Which assets to load and their mapping structures
    # Each entry maps a GUID to its configuration:
    #   - path: Base path within the asset to the mapping structure
    #   - mappings: Dict of dataset_name -> path template for text lookup
    #               Use {} as placeholder for the literal value
    #   - buff_texts: Path to buff text structs configuration
    CONFIG_ASSETS: t.ClassVar[dict[int, dict[str, t.Any]]] = {
        142928: {  # ItemInfotipTextFeature
            "path": "ItemInfotipTextFeature.BuffUpgradeTextAndIcons",
            "buff_texts": "ItemInfotipTextFeature.BuffUpgradeTextAndIcons",  # Direct access to buff text structs
            "mappings": {
                # Buff upgrade types - most common mappings
                "BuffUpgradeType": "{}.Text",
                # Need attribute types (Population, Money, Happiness, Health, etc.)
                "NeedAttributeType": "BuffAdditionalNeedAttributes.Attributes.{}.Text",
            },
            # Some buffs have variant text for different contexts
            "variants": {
                "BuffConstructionCost": ["ShipyardText", "RecruitmentText", "SingleShipText", "SingleTroopText"],
                "BuffConstructionSpeed": ["ShipyardText", "RecruitmentText", "SingleShipText", "SingleTroopText"],
                "BuffOutputWorkforce": ["AdditionalText"],
                "BuffPassiveTradeBonus": ["RewardText"],
                "BuffInfectableImmunity": ["AreaText"],
                "BuffCanUseTerrain": ["ForestText", "MeadowText", "MarshText"],
                "BuffAdditionalFactoryOutput": [
                    "TextWithSpecifiedProduct",
                    "TextWithSpecifiedProductEveryCycle",
                    "ForceProductSameAsFactoryOutputText",
                    "ForceProductSameAsFactoryOutputEveryCycleText",
                ],
                "BuffFactoryInput": ["InputAmountUpgradeText", "InputReplaceInputText"],
            },
        },
        6000017: {  # ItemBalancing
            "path": "ItemConfig",
            "mappings": {
                "Rarity": "RarityVisualization.{}.Text",
                "ItemNiche": "NicheVisualization.{}.Text",
                "ItemAllocation": "AllocationText.{}.Text",
                "Scope": "ScopeVisualization.{}.Text",
                "SocketExclusiveGroup": "ExclusiveGroupText.{}.Text",
                "ItemType": "ItemTypeText.{}.Text",
                "NotSockableReason": "NotSockableText.{}.Text",
            },
        },
        52456: {  # BuffConfig (if it exists)
            "path": "BuffCategory",
            "mappings": {"BuffCategoryType": "{}.Name"},
        },
    }

    def __init__(self, assets: AssetCache):
        """Initialize the UI text cache.

        Args:
            assets: The asset cache to load configuration assets from
        """
        self.assets = assets
        self.mappings: dict[tuple[str, str], UITextMapping] = {}
        self.buff_text_structs: dict[str, t.Any] = {}  # Maps buff type names to their text structs
        self.incident_type_mapping: dict[str, Asset] = {}  # Maps InfectionType literal to IncidentInfection asset
        self.region_mapping: dict[str, Asset] = {}  # Maps Region literal to Region asset
        self._load_configurations()

    def _load_configurations(self):
        """Load all configuration assets and build lookup tables."""
        for guid, config in self.CONFIG_ASSETS.items():
            try:
                asset = self.assets.get(guid)
                if asset is None:
                    logger.debug(f"Configuration asset {guid} not found, skipping")
                    continue

                logger.info(f"Loading UI text mappings from asset {guid}")
                self._load_asset_mappings(asset, config)

                # Load buff text structs if configured
                if "buff_texts" in config:
                    logger.info(f"Loading buff texts from asset {guid}")
                    self._load_buff_texts(asset, config)
                else:
                    logger.debug(f"No buff_texts configured for asset {guid}")

            except Exception as e:
                logger.warning(f"Failed to load UI text mappings from asset {guid}: {e}")

        # Load incident type mappings from IncidentInfection template
        self._load_incident_type_mappings()

        # Load region mappings from Region template
        self._load_region_mappings()

    def _load_asset_mappings(self, asset: Asset, config: dict[str, t.Any]):
        """Load mappings from a single configuration asset.

        Args:
            asset: The configuration asset to load from
            config: Configuration dict with path, mappings, and optional variants
        """
        base_path = config["path"]
        variants_config = config.get("variants", {})

        for dataset_name, text_path_template in config["mappings"].items():
            # Get the dataset to iterate over its literals
            dataset = self.assets.datasets.get(dataset_name)
            if dataset is None:
                logger.debug(f"Dataset {dataset_name} not found, skipping")
                continue

            # For each literal in the dataset, extract text/icon
            for literal in dataset.literals:
                try:
                    mapping = self._extract_mapping(asset, base_path, literal, text_path_template, variants_config)
                    if mapping is not None:
                        key = (dataset_name, literal)
                        self.mappings[key] = mapping
                        logger.debug(f"Mapped {dataset_name}.{literal} -> text_id={mapping.text_id}")

                except Exception as e:
                    logger.debug(f"Failed to extract mapping for {dataset_name}.{literal}: {e}")

    def _get_icon(self, icon_attr: NamedElement[t.Any] | None) -> FileNameAttribute | None:
        if icon_attr is None:
            return None

        # Icon can be either:
        # 1. A ReferenceAttribute pointing to an Icon asset with IconFilename property
        # 2. A FileNameAttribute directly

        # Handle ReferenceAttribute (points to Icon asset)
        if isinstance(icon_attr, ReferenceAttribute):
            # Follow the reference to get the Icon asset
            try:
                icon_asset = icon_attr()
                if icon_asset is not None:
                    # Get the FileNameAttribute from the Icon asset
                    # Try Standard.IconFilename first (most common)
                    icon_filename = icon_asset.find("Standard.IconFilename")
                    if icon_filename is not None:
                        return icon_filename
                    else:
                        # Fallback to just IconFilename
                        return icon_asset.find("IconFilename")
            except Exception:
                pass

        # Handle FileNameAttribute or primitive directly
        else:
            try:
                # Check if it's a FileNameAttribute
                if isinstance(icon_attr, FileNameAttribute):
                    return icon_attr
            except Exception:
                pass

        return None

    def _extract_mapping(
        self, asset: Asset, base_path: str, literal: str, text_path_template: str, variants_config: dict[str, list[str]]
    ) -> UITextMapping | None:
        """Extract text and icon mapping for a single dataset literal.

        Args:
            asset: The configuration asset
            base_path: Base path within the asset
            literal: The dataset literal value
            text_path_template: Template for the text path (with {} placeholder)
            variants_config: Configuration for variant text fields

        Returns:
            UITextMapping if successful, None otherwise
        """
        # Build the path to the text attribute
        text_path = text_path_template.format(literal)
        full_text_path = f"{base_path}.{text_path}"

        # Navigate to the text ID
        text_attr = asset.find(full_text_path)
        if not isinstance(text_attr, TextAttribute):
            return None

        text_value: Text = text_attr()

        # If it's a Text object, extract its ID and store the object
        # Text attributes return Text objects which have an .id property
        text_obj = None
        text_id = None
        if hasattr(text_value, "id"):
            text_id = text_value.id
            text_obj = text_value

        # Try to find icon (usually at same level, replace .Text/.Name with .Icon)
        icon_path = full_text_path.replace(".Text", ".Icon").replace(".Name", ".Icon")
        icon_attr = asset.find(icon_path)
        icon_file_attr = self._get_icon(icon_attr)

        # Extract variant text if configured
        variants: dict[str, int] = {}
        if literal in variants_config:
            variant_fields = variants_config[literal]
            struct_path = f"{base_path}.{literal}"

            for variant_name in variant_fields:
                variant_path = f"{struct_path}.{variant_name}"
                attr = asset.find(variant_path)
                variant_attr = attr if isinstance(attr, TextAttribute) else None
                if variant_attr is not None:
                    try:
                        variant_value = variant_attr()
                        if variant_value is not None:
                            # If it's a Text object, extract its ID
                            variant_id = variant_value.id if hasattr(variant_value, "id") else variant_value
                            variants[variant_name] = variant_id
                    except Exception:
                        pass

        return UITextMapping(text_id=text_id, text=text_obj, icon=icon_file_attr, variants=variants)

    def get_ui_text(self, dataset_name: str, literal: str) -> UITextMapping | None:
        """Look up UI text mapping for a dataset literal.

        Args:
            dataset_name: Name of the dataset (e.g., "Rarity", "ItemNiche", "IncidentType", "Region")
            literal: The literal value from the dataset (e.g., "Legendary", "Finance", "Disease", "Roman")

        Returns:
            UITextMapping with text and optional icon, or None if not found
        """
        # Special case: IncidentType uses asset text directly
        if dataset_name == "IncidentType":
            return self._get_incident_type_text(literal)

        # Special case: Region uses asset text directly
        if dataset_name == "Region":
            return self._get_region_text(literal)

        # Standard case: lookup from pre-loaded mappings
        return self.mappings.get((dataset_name, literal))

    def _get_incident_type_text(self, literal: str) -> UITextMapping | None:
        """Get incident type text from IncidentInfection assets directly.

        Args:
            literal: The incident type literal (e.g., "Disease", "Fire")

        Returns:
            UITextMapping with text from the asset, or None if not found
        """
        # Look up the asset from the pre-built mapping
        asset = self.incident_type_mapping.get(literal)
        if asset is None:
            return None

        # Get the asset's text
        text = None
        if hasattr(asset, "text") and asset.text is not None:
            text = asset.text

        # Try to get icon from Standard.IconFilename (if available)
        icon_file = None
        try:
            icon_attr = asset.find("Standard.IconFilename")
            if icon_attr is not None:
                icon_file = self._get_icon(icon_attr)
        except Exception:
            pass

        # Create mapping with text and optional icon
        if text:
            return UITextMapping(text=text, icon=icon_file)

        return None

    def _get_region_text(self, literal: str) -> UITextMapping | None:
        """Get region text from Region assets directly.

        Args:
            literal: The region literal (e.g., "Roman", "Celtic")

        Returns:
            UITextMapping with text from the asset, or None if not found
        """
        # Look up the asset from the pre-built mapping
        asset = self.region_mapping.get(literal)
        if asset is None:
            return None

        # Get the asset's text
        text = None
        if hasattr(asset, "text") and asset.text is not None:
            text = asset.text

        # Try to get icon from Standard.IconFilename (if available)
        icon_file = None
        try:
            icon_attr = asset.find("Standard.IconFilename")
            if icon_attr is not None:
                icon_file = self._get_icon(icon_attr)
        except Exception:
            pass

        # Create mapping with text and optional icon
        if text is not None:
            return UITextMapping(text=text, icon=icon_file)

        return None

    def get_text_id(self, dataset_name: str, literal: str) -> int | None:
        """Get just the text ID for a dataset literal.

        Args:
            dataset_name: Name of the dataset
            literal: The literal value from the dataset

        Returns:
            Text ID (negative number), or None if not found
        """
        mapping = self.get_ui_text(dataset_name, literal)
        return mapping.text_id if mapping else None

    def __len__(self) -> int:
        """Return the number of mappings loaded."""
        return len(self.mappings)

    def __repr__(self) -> str:
        return f"UITextCache({len(self.mappings)} mappings)"

    def _load_buff_texts(self, asset: "Asset", config: dict[str, t.Any]):
        """Load buff text structs from configuration asset.

        Args:
            asset: The configuration asset
            config: Configuration dict with buff_texts path
        """
        buff_texts_path = config["buff_texts"]
        variants_config = config.get("variants", {})

        try:
            # Navigate to the buff texts struct
            buff_texts_struct = asset.find(buff_texts_path)
            logger.debug(
                f"buff_texts_struct: {buff_texts_struct}, hasattr properties: {hasattr(buff_texts_struct, 'properties') if buff_texts_struct is not None else False}"
            )
            if buff_texts_struct is None:
                logger.debug(f"Buff texts path {buff_texts_path} not found")
                return

            # DictAttribute stores items in .value (a dict)
            if isinstance(buff_texts_struct, DictAttribute) and buff_texts_struct.value is not None:
                logger.debug(f"Found {len(buff_texts_struct)} entries in buff texts struct")
                for buff_type_name, buff_struct in buff_texts_struct.value.items():
                    # Store the struct (which is a Property) with its variant text field names
                    variant_fields = variants_config.get(buff_type_name, [])
                    self.buff_text_structs[buff_type_name] = {"struct": buff_struct, "variants": variant_fields}
                    logger.debug(f"Loaded buff text struct: {buff_type_name} with variants: {variant_fields}")
            else:
                logger.warning(
                    f"buff_texts_struct has no value attribute or it's empty. Type: {type(buff_texts_struct)}"
                )

        except Exception as e:
            logger.warning(f"Failed to load buff texts from {buff_texts_path}: {e}")

    def _load_incident_type_mappings(self) -> None:
        """Build mapping from InfectionType literals to IncidentInfection assets.

        This allows get_ui_text("IncidentType", "Disease") to retrieve text
        from the corresponding IncidentInfection asset.
        """
        if "IncidentInfection" not in self.assets.templates:
            logger.debug("IncidentInfection template not found, skipping incident type mappings")
            return

        template = self.assets.templates["IncidentInfection"]
        if template is None:
            logger.error("Template IncidentInfection not found")
            return

        logger.info(f"Loading incident type mappings from {len(template.assets)} IncidentInfection assets")

        for asset in template.assets:
            # Get the InfectionType value (e.g., "Fire", "Disease", "Plague")
            infection_type_attr = asset.find("IncidentInfection.InfectionType")
            if infection_type_attr is None:
                continue

            infection_type = infection_type_attr()  # pyright: ignore
            if isinstance(infection_type, str) and asset.text is not None:
                # Map the literal value to the asset
                self.incident_type_mapping[infection_type] = asset
                logger.debug(f"Mapped IncidentType '{infection_type}' to asset {asset.guid}")

        logger.info(f"Loaded {len(self.incident_type_mapping)} incident type mappings")

    def _load_region_mappings(self) -> None:
        """Build mapping from Region literals to Region assets.

        This allows get_ui_text("Region", "Roman") to retrieve text
        from the corresponding Region asset.
        """
        if "Region" not in self.assets.templates:
            logger.debug("Region template not found, skipping region mappings")
            return

        template = self.assets.templates["Region"]
        if template is None:
            logger.error("Template Region not found")
            return

        logger.info(f"Loading region mappings from {len(template.assets)} Region assets")

        for asset in template.assets:
            # Get the RegionID value (e.g., "Roman", "Celtic")
            region_id_attr = asset.find("Region.RegionID")
            if region_id_attr is None:
                continue

            region_id = region_id_attr()  # type: ignore
            if isinstance(region_id, str) and asset.text is not None:
                # Map the literal value to the asset
                self.region_mapping[region_id] = asset
                logger.debug(f"Mapped Region '{region_id}' to asset {asset.guid}")

        logger.info(f"Loaded {len(self.region_mapping)} region mappings")

    def get_buff_type_name(self, property_name: str, attr_name: str) -> str | None:
        """Automatically derive buff type name from property and attribute names.

        Args:
            property_name: Name of the property (e.g., "FactoryUpgrade", "MovementUpgrade")
            attr_name: Name of the attribute (e.g., "ProductivityUpgrade", "AdditionalOutput")

        Returns:
            Buff type name if found, None otherwise
        """
        # Strip "Upgrade" suffix from property name
        property_base = property_name[: -len("Upgrade")] if property_name.endswith("Upgrade") else property_name

        # Strip "InPercent", "Percent", and "Upgrade" suffixes from attribute name
        attr_base = attr_name
        if attr_base.endswith("InPercent"):
            attr_base = attr_base[: -len("InPercent")]
        elif attr_base.endswith("Percent"):
            attr_base = attr_base[: -len("Percent")]
        if attr_base.endswith("Upgrade"):
            attr_base = attr_base[: -len("Upgrade")]
        # Also handle typo in game data
        if attr_base.endswith("Upgrage"):
            attr_base = attr_base[: -len("Upgrage")]

        # Strip "Buff" prefix if already present
        if attr_base.startswith("Buff"):
            attr_base = attr_base[4:]

        ui_keys = self.buff_text_structs.keys()

        # Special case mappings for non-standard naming patterns
        # Only include cases where Buff + attr_base doesn't work
        special_mappings = {
            # FactoryUpgrade - non-standard names
            ("Factory", "AdditionalOutput"): "BuffAdditionalFactoryOutput",
            ("Factory", "InputAmount"): "BuffFactoryInput",
            ("Factory", "ReplaceInputs"): "BuffFactoryReplaceInput",
            ("Factory", "CanUseMarsh"): "BuffCanUseTerrain",  # All terrain types -> same buff
            ("Factory", "CanUseForest"): "BuffCanUseTerrain",
            ("Factory", "CanUseMeadow"): "BuffCanUseTerrain",
            # RecruitmentUpgrade - maps to Construction buffs
            ("Recruitment", "RecruitmentCost"): "BuffConstructionCost",
            ("Recruitment", "RecruitmentSpeed"): "BuffConstructionSpeed",
            # MaintenanceUpgrade
            ("Maintenance", "MaintenanceFactor"): "BuffMaintenance",
            ("Maintenance", "WorkforceMaintenanceFactor"): "BuffWorkforceAmount",
            ("Maintenance", "ReplaceWorkforce"): "BuffReplaceWorkforceText",
            # WarehouseUpgrade
            ("Warehouse", "StorageCapacityModifier"): "BuffIslandStorage",
            ("Warehouse", "AdditionalLoadingSpeed"): "BuffLoadingSpeed",
            # HealthUpgrade
            ("Health", "BaseHealth"): "BuffHitpoints",
            # CityInstitutionUpgrade
            ("CityInstitution", "ResolverResolveDuration"): "BuffCityInstitutionResolverDuration",
            ("CityInstitution", "ResolverRepairDuration"): "BuffCityInstitutionRepairDuration",
            # IncidentInfectableUpgrade
            ("IncidentInfectable", "ResistanceThreshold"): "BuffInfectableResistanceThreshold",
            ("IncidentInfectable", "IncidentImmunity"): "BuffInfectableImmunity",
            # AreaBuff - BlockedIncidentType also maps to BuffInfectableImmunity
            ("AreaBuff", "BlockedIncidentType"): "BuffInfectableImmunity",
            ("AreaBuff", "RadiusEffectRangeTarget"): "BuffEffectRadius",
            # IrrigationUpgrade
            ("Irrigation", "PipeCapacity"): "BuffIrrigationCapacity",
            # ModuleOwnerUpgrade
            ("ModuleOwner", "ModuleLimit"): "BuffModuleLimitChange",
            # AqueductUpgrade - different naming
            ("Aqueduct", "AqueductConsumedWater"): "BuffAqueductConsumption",
            ("Aqueduct", "AqueductWaterSupply"): "BuffAqueductProduction",
            # ResidenceUpgrade - NeedProvided has special text
            ("Residence", "NeedProvidedNeedAttributes"): "BuffAdditionalNeedAttributes",
            ("Residence", "ProvidedNeedUpgrade"): "BuffResidenceProvidedNeedText",
            # MovementUpgrade - all map to BuffSpeed
            ("Movement", "BaseSpeed"): "BuffSpeed",
            ("Movement", "ReduceCargoImpact"): "BuffReduceSpeedImpactOfWeight",
            ("Movement", "ReduceDamageImpact"): "BuffReduceSpeedImpactOfDamage",
            ("Movement", "ReduceNegativeWindImpact"): "BuffReduceNegativeSpeedImpactOfWind",
            # RepairCraneUpgrade
            ("RepairCrane", "HealPerMinute"): "BuffHealRate",
            # WorkforceModifier - maps to specific buff
            ("Building", "WorkforceModifier"): "BuffWorkforceAmount",
            ("Building", "AdditionalAttributes"): "BuffAdditionalNeedAttributes",
            ("Building", "AdditionalWorkforces"): "BuffOutputWorkforce",
            # AreaPassiveTradeUpgrade
            ("AreaPassiveTrade", "PassiveTradeReward"): "BuffPassiveTradeBonus",
            ("AreaPassiveTrade", "PassiveTradeProfitModifier"): "BuffPassiveTradeBonus",
            # AreaFestivalAttributeUpgrade
            ("AreaFestivalAttribute", "AdditionalPercentage"): "BuffFestivalAttributePercentage",
            # AreaMaintenanceUpgrade
            ("AreaMaintenance", "MeshGraphUpkeep"): "BuffMeshGraphUpkeep",
        }

        key = (property_base, attr_base)

        if key in special_mappings:
            return special_mappings[key]

        # Try pattern 1: Buff{attr_base}
        buff_type_name = f"Buff{attr_base}"
        if buff_type_name in ui_keys:
            return buff_type_name

        # Try pattern 2: Buff{property_base}{attr_base}
        buff_type_name = f"Buff{property_base}{attr_base}"
        if buff_type_name in ui_keys:
            return buff_type_name

        # Pattern 3: Try with "Upgrade" suffix (e.g., BuffBaseHealthUpgrade)
        buff_type_name = f"Buff{attr_base}Upgrade"
        if buff_type_name in ui_keys:
            return buff_type_name

        # Fallback: search for buff types containing attr_base
        for buff_type_name in ui_keys:
            if attr_base in buff_type_name:
                return buff_type_name

        return None

    def format_buff_text(self, buff_type: str, list_item: t.Any) -> Text | None:
        """Format buff text with placeholders filled from list item values.

        Args:
            buff_type: The buff type (e.g., "BuffAdditionalFactoryOutput")
            list_item: The ListItem containing the buff data

        Returns:
            Formatted text string, or None if formatting fails
        """
        # Get the buff text struct for this buff type
        buff_info = self.buff_text_structs.get(buff_type)
        logger.debug(f"format_buff_text({buff_type}) - found in buff_text_structs: {buff_info is not None}")
        if not buff_info:
            logger.debug(f"No buff text struct found for {buff_type}")
            return None

        try:
            # BuffAdditionalFactoryOutput special handling
            if buff_type == "BuffAdditionalFactoryOutput":
                return self._format_additional_factory_output(list_item, buff_info)

            # BuffResidenceProvidedNeedText special handling
            if buff_type == "BuffResidenceProvidedNeedText":
                return self._format_residence_provided_need(list_item, buff_info)

            # BuffOutputWorkforce special handling
            if buff_type == "BuffOutputWorkforce":
                return self._format_output_workforce(list_item, buff_info)

            # BuffPassiveTradeBonus special handling
            if buff_type == "BuffPassiveTradeBonus":
                return self._format_passive_trade_bonus(list_item, buff_info)

            # BuffEffectRadius special handling
            if buff_type == "BuffEffectRadius":
                return self._format_effect_radius(list_item, buff_info)

            # Add more buff types here as needed

            return None
        except Exception as e:
            logger.debug(f"Failed to format buff text for {buff_type}: {e}")
            return None

    def _format_additional_factory_output(self, list_item: t.Any, buff_info: dict[str, t.Any]) -> Text | None:
        """Format BuffAdditionalFactoryOutput text with actual values."""
        try:
            buff_struct = buff_info["struct"]

            # Get values from the list item
            amount_attr = list_item.find("Amount")
            amount = amount_attr() if amount_attr is not None else None
            product_attr = list_item.find("Product")
            cycle_attr = list_item.find("AdditionalOutputCycle")
            cycle = cycle_attr() if cycle_attr is not None else 1
            force_same_attr = list_item.find("ForceProductSameAsFactoryOutput")
            force_same = force_same_attr() if force_same_attr is not None else False

            if amount is None:
                return None

            # Format amount as integer if possible
            amount_str = str(int(amount)) if amount == int(amount) else str(amount)

            # Determine which variant text to use and get the text from the struct
            if force_same:
                if cycle is not None and cycle > 1:
                    text_attr = buff_struct.find("ForceProductSameAsFactoryOutputText")
                    if isinstance(text_attr, TextAttribute):
                        return text_attr().format([amount_str, str(int(cycle))])
                else:
                    text_attr = buff_struct.find("ForceProductSameAsFactoryOutputEveryCycleText")
                    if isinstance(text_attr, TextAttribute):
                        return text_attr().format([amount_str])
            else:
                # Product is specified
                product_name = ""
                if product_attr is not None:
                    product_asset = product_attr()
                    if product_asset is not None and hasattr(product_asset, "text") and product_asset.text is not None:
                        product_name = product_asset.text

                if cycle is not None and cycle > 1:
                    text_attr = buff_struct.find("TextWithSpecifiedProduct")
                    if isinstance(text_attr, TextAttribute):
                        return text_attr().format([amount_str, product_name, str(int(cycle))])
                else:
                    text_attr = buff_struct.find("TextWithSpecifiedProductEveryCycle")
                    if isinstance(text_attr, TextAttribute):
                        return text_attr().format([amount_str, product_name])

            return None
        except Exception as e:
            logger.debug(f"Failed to format BuffAdditionalFactoryOutput: {e}")
            return None

    def _format_residence_provided_need(self, list_item: t.Any, buff_info: dict[str, t.Any]) -> Text | None:
        """Format BuffResidenceProvidedNeedText with the need name.

        Args:
            list_item: ListItem with ProvidedNeed reference
            buff_info: Buff info dict with struct

        Returns:
            Formatted text string, or None if formatting fails
        """
        try:
            buff_struct = buff_info["struct"]

            # Get the ProvidedNeed reference from the list item
            need_asset = list_item.find_ref("ProvidedNeed")
            if need_asset is None:
                return None

            need_product = need_asset.find("Need.NeedProduct")

            # Get the need name from the asset
            # Try text first, then fall back to Standard.Name
            need_name = None
            if need_product is not None and hasattr(need_product(), "text"):
                need_name = need_product().text

            if need_name is None:
                return None

            # Get the text template from buff struct (it's a Text directly, not a nested attribute)
            if isinstance(buff_struct, TextAttribute):
                # Format with the need name (can be Text or str)
                return buff_struct().format([need_name])

            return None
        except Exception as e:
            logger.debug(f"Failed to format BuffResidenceProvidedNeedText: {e}")
            return None

    def _format_output_workforce(self, list_item: t.Any, buff_info: dict[str, t.Any]) -> Text | None:
        """Format BuffOutputWorkforce text with the workforce name.

        Args:
            list_item: ListItem with WorkforceGUID reference
            buff_info: Buff info dict with struct

        Returns:
            Formatted text string, or None if formatting fails
        """
        try:
            buff_struct = buff_info["struct"]

            # Get the WorkforceGUID reference from the list item
            workforce_asset = list_item.find_ref("WorkforceGUID")
            if workforce_asset is None:
                return None

            # Get the workforce name from the asset's text
            workforce_name = None
            if hasattr(workforce_asset, "text") and workforce_asset.text is not None:
                workforce_name = workforce_asset.text

            # Fallback to Standard.Name if text is not available
            if workforce_name is None:
                name_attr = workforce_asset.find("Standard.Name")
                if name_attr is not None:
                    workforce_name = name_attr()

            if workforce_name is None:
                return None

            # Get the AdditionalText variant from buff struct
            additional_text_attr = buff_struct.find("AdditionalText")
            if isinstance(additional_text_attr, TextAttribute):
                # Format with the workforce name (can be Text or str)
                return additional_text_attr().format([workforce_name])

            return None
        except Exception as e:
            logger.debug(f"Failed to format BuffOutputWorkforce: {e}")
            return None

    def _format_passive_trade_bonus(self, list_item: t.Any, buff_info: dict[str, t.Any]) -> Text | None:
        """Format BuffPassiveTradeBonus text with actual values.

        Template: "{}t {} gained, for every {}t {} sold"

        Args:
            list_item: ListItem with RewardProduct, RewardAmount, SoldProduct, SoldAmount
            buff_info: Dict with 'struct' and 'variants' keys

        Returns:
            Formatted Text object or None if formatting fails
        """
        try:
            buff_struct = buff_info["struct"]

            # Step 1: Extract numeric amounts from list item
            reward_amount_attr = list_item.find("RewardAmount")
            reward_amount = reward_amount_attr() if reward_amount_attr else None
            sold_amount_attr = list_item.find("SoldAmount")
            sold_amount = sold_amount_attr() if sold_amount_attr else None

            if reward_amount is None or sold_amount is None:
                return None

            # Step 2: Extract product references and resolve to assets
            reward_product_asset = list_item.find_ref("RewardProduct")
            sold_product_asset = list_item.find_ref("SoldProduct")

            # Step 3: Get product names (Text objects) from referenced assets
            reward_product_name = None
            if reward_product_asset and hasattr(reward_product_asset, "text") and reward_product_asset.text:
                reward_product_name = reward_product_asset.text

            sold_product_name = None
            if sold_product_asset and hasattr(sold_product_asset, "text") and sold_product_asset.text:
                sold_product_name = sold_product_asset.text

            if reward_product_name is None or sold_product_name is None:
                return None

            # Step 4: Format amounts as integers (no decimals)
            reward_amount_str = str(int(reward_amount)) if reward_amount == int(reward_amount) else str(reward_amount)
            sold_amount_str = str(int(sold_amount)) if sold_amount == int(sold_amount) else str(sold_amount)

            # Step 5: Get the RewardText variant from buff_struct
            text_attr = buff_struct.find("RewardText")
            if text_attr is None:
                logger.debug("RewardText not found in buff_struct for BuffPassiveTradeBonus")
                return None

            # Step 6: Format the text with all 4 values in order
            # Template: "{}t {} gained, for every {}t {} sold"
            # Args: [reward_amount, reward_product, sold_amount, sold_product]
            formatted_text = text_attr().format(
                [
                    reward_amount_str,  # {}t (reward amount)
                    reward_product_name,  # {} (reward product name - Text object)
                    sold_amount_str,  # {}t (sold amount)
                    sold_product_name,  # {} (sold product name - Text object)
                ]
            )

            return formatted_text

        except Exception as e:
            logger.debug(f"Failed to format BuffPassiveTradeBonus: {e}")
            return None

    def _format_effect_radius(self, list_item: t.Any, buff_info: dict[str, t.Any]) -> Text | None:
        """Format BuffEffectRadius with building target name.

        Template: "Effect range of {}"
        Placeholder: [target_building_name]

        Structure:
        - list_item.Target (ReferenceAttribute) → Building asset

        Example: "Effect range of Markets"

        Args:
            list_item: ListItem from RadiusEffectRangeTarget containing Target reference
            buff_info: Buff info dict with struct containing the text template

        Returns:
            Formatted Text object or None if formatting fails
        """
        try:
            # Get the target building reference
            target_asset = list_item.find_ref("Target")
            if target_asset is None:
                return None

            # Get building name from asset text
            target_name = None
            if hasattr(target_asset, "text") and target_asset.text is not None:
                target_name = target_asset.text

            if not target_name:
                return None

            # Get text template from buff struct
            struct = buff_info["struct"]
            text_attr = struct.find("Text")
            if not text_attr:
                return None

            text_obj = text_attr()
            if not text_obj:
                return None

            # Format with target name
            # Text is "Effect range of {}", format with [target_name]
            if hasattr(text_obj, "format"):
                return text_obj.format([target_name])

            return text_obj

        except Exception as e:
            logger.debug(f"Failed to format BuffEffectRadius: {e}")
            return None

    def _format_replace_workforce(self, dict_attr: DictAttribute, buff_info: dict[str, t.Any]) -> Text | None:
        """Format BuffReplaceWorkforceText with old and new workforce names.

        Args:
            dict_attr: The ReplaceWorkforce DictAttribute containing OldWorkforce and NewWorkforce
            buff_info: Buff info dict with struct containing the text template

        Returns:
            Formatted Text object or None if formatting fails
        """
        try:
            buff_struct = buff_info["struct"]

            # Step 1: Get OldWorkforce reference from dict_attr
            old_workforce_attr = dict_attr["OldWorkforce"]
            if not old_workforce_attr or not isinstance(old_workforce_attr, ReferenceAttribute):
                return None

            # Step 2: Get NewWorkforce reference from dict_attr
            new_workforce_attr = dict_attr["NewWorkforce"]
            if not new_workforce_attr or not isinstance(new_workforce_attr, ReferenceAttribute):
                return None

            # Step 3: Resolve references to get Workforce assets
            old_workforce_asset = old_workforce_attr()
            new_workforce_asset = new_workforce_attr()

            if not old_workforce_asset or not new_workforce_asset:
                return None

            # Step 4: Extract workforce names (Text objects) from assets
            old_workforce_name = None
            if hasattr(old_workforce_asset, "text") and old_workforce_asset.text is not None:
                old_workforce_name = old_workforce_asset.text
            else:
                # Fallback to Standard.Name
                name_attr = old_workforce_asset.find("Standard.Name")
                if name_attr is not None:
                    old_workforce_name = name_attr()

            new_workforce_name = None
            if hasattr(new_workforce_asset, "text") and new_workforce_asset.text is not None:
                new_workforce_name = new_workforce_asset.text
            else:
                name_attr = new_workforce_asset.find("Standard.Name")
                if name_attr is not None:
                    new_workforce_name = name_attr()

            if not old_workforce_name or not new_workforce_name:
                return None

            # Step 5: Get the text template from buff_struct and format
            # BuffReplaceWorkforceText should be a TextAttribute in the struct
            if isinstance(buff_struct, TextAttribute):
                # Format with workforce names: [old_workforce, new_workforce]
                return buff_struct().format([new_workforce_name, old_workforce_name])

            return None

        except Exception as e:
            logger.debug(f"Failed to format BuffReplaceWorkforceText: {e}")
            return None

    def format_product_list_item(self, list_item: ListItem, add_sign: bool = False) -> BuffUI | None:
        """Format Product list item name.

        Args:
            list_item: ListItem with Product | Ingredient (ReferenceAttribute) and Amount (PrimitiveAttribute)

        Returns:
            BuffUi, or None if formatting fails
        """
        try:
            # Get the Product reference from the list item
            product_asset = list_item.find_ref("Product")
            if product_asset is None:
                product_asset = list_item.find_ref("Ingredient")

            if product_asset is None:
                return None

            # Get the product name from the asset's text
            product_name = product_asset.text

            # Fallback to Standard.Name if text is not available
            if product_name is None:
                name_attr = product_asset.find("Standard.Name")
                if name_attr:
                    val = name_attr()  # pyright: ignore
                    if isinstance(val, str):
                        product_name = val

            if product_name is None:
                return None

            value_attr = list_item.find("Amount")
            if value_attr is None:
                return None

            value = value_attr()  # pyright: ignore
            if not isinstance(value, int) or value == 0:
                return None

            return BuffUI(product_asset.icon, product_name, f"+{value}" if add_sign else str(value))
        except Exception as e:
            logger.debug(f"Failed to format product list item: {e}")
            return None

    def format_product_list(self, list: ListAttribute, add_sign: bool = False) -> list[BuffUI] | None:
        result: list[BuffUI] = []

        for item in list:
            buff_ui = self.format_product_list_item(item, add_sign)

            if buff_ui is not None:
                result.append(buff_ui)

        return result if len(result) > 0 else None

    def create_buff_ui_flags(
        self, property_name: str, attr_name: str, flags_attr: FlagsAttribute
    ) -> list[BuffUI] | None:
        buff_type = self.get_buff_type_name(property_name, attr_name)
        if flags_attr.value is None or buff_type is None or buff_type not in self.buff_text_structs:
            return None

        buff_info = self.buff_text_structs[buff_type]
        buff_struct = buff_info["struct"]

        # Select appropriate text variant based on context
        text_attr = None
        icon_attr = None

        if buff_type == "BuffInfectableImmunity":
            # Use Text variant for BuildingBuff context, AreaText for AreaBuff context
            logger.debug(f"BuffInfectableImmunity detected: property_name={property_name}, attr_name={attr_name}")
            if property_name == "IncidentInfectableUpgrade":
                # BuildingBuff.IncidentInfectableUpgrade.IncidentImmunity
                logger.debug("Using Text variant for BuildingBuff context")
                text_attr = buff_struct.find("Text")
                icon_attr = buff_struct.find("Icon")
                logger.debug(f"text_attr={text_attr}, icon_attr={icon_attr}")
            else:
                # AreaBuff.BlockedIncidentType
                logger.debug("Using AreaText variant for AreaBuff context")
                text_attr = buff_struct.find("AreaText")
                area_icon = buff_struct.find("AreaIcon")
                icon_attr = area_icon if area_icon is not None else buff_struct.find("Icon")
                logger.debug(f"text_attr={text_attr}, icon_attr={icon_attr}")
        else:
            # Default: try AreaText first (existing behavior for other buff types)
            text_attr = buff_struct.find("AreaText")
            icon_attr = buff_struct.find("Icon")

        if text_attr is None:
            logger.debug(f"No text variant found for {buff_type} with property={property_name}")
            return None

        text_template: Text = text_attr()

        result: list[BuffUI] = []
        for literal in flags_attr.value:
            # Get icon from buff type mapping
            immune_icon_attr = buff_struct.find(f"Icons.{literal}.ImmuneIcon")
            icon_obj = self._get_icon(immune_icon_attr)

            mapping = self.get_ui_text("IncidentType", literal)
            formatted_text = (
                text_template.format([mapping.text]) if mapping is not None and mapping.text is not None else None
            )

            result.append(BuffUI(icon=icon_obj, text=formatted_text))

        if len(result) == 0:
            return None

        return result

    def create_buff_ui_dict(
        self, property_name: str, attr_name: str, dict_attr: DictAttribute, in_additional_effect: bool = False
    ) -> list[BuffUI] | None:
        """Create BuffUI objects for DictAttribute with AmountOrPercent structure.

        This method handles DictAttributes that contain multiple attributes with AmountOrPercent values,
        such as:
        - BuildingUpgrade.AdditionalAttributes (Population, Money, Happiness, etc.)
        - ResidenceUpgrade.NeedProvidedNeedAttributes.AdditionalNeedAttributes
        - ResidenceUpgrade.ReplaceWorkforce

        Args:
            property_name: Property name (e.g., "BuildingUpgrade", "ResidenceUpgrade")
            attr_name: Attribute name (e.g., "AdditionalAttributes", "AdditionalNeedAttributes")
            dict_attr: The DictAttribute containing the values
            parent_attr: Optional parent attribute for contextual formatting (e.g., NeedProvidedNeedAttributes)

        Returns:
            List of BuffUI objects for non-zero values
        """
        # Special handling for ReplaceWorkforce (NOT a dataset-based dict)
        if attr_name == "ReplaceWorkforce":
            return self._create_buff_ui_replace_workforce(property_name, attr_name, dict_attr)

        # Special handling for MeshGraphUpkeep (dataset-based dict)
        if attr_name == "MeshGraphUpkeep":
            return self._create_buff_ui_mesh_graph_upkeep(property_name, attr_name, dict_attr)

        result: list[BuffUI] = []

        buff_info = self.buff_text_structs.get("BuffAdditionalNeedAttributes")
        if buff_info is None:
            return None

        buff_struct = buff_info["struct"]
        if not isinstance(buff_struct, DictAttribute):
            return None

        try:
            args: list[Text] = []
            items: list[tuple[str, Attribute[t.Any, t.Any]]] = []
            # Get the items to process
            # Special handling for NeedProvidedNeedAttributes - get AdditionalNeedAttributes
            if dict_attr.identifier == "NeedProvidedNeedAttributes":
                additional_attrs = dict_attr["AdditionalNeedAttributes"]
                if additional_attrs and isinstance(additional_attrs, DictAttribute) and additional_attrs.value:
                    items = list(additional_attrs.value.items())
                else:
                    items = []

                provided_list = dict_attr["ChangeNeedAttributesOf"]

                if isinstance(provided_list, ListAttribute):
                    for item in provided_list:
                        product = item.find_ref("ProvidedProduct")
                        if product is not None and product.text is not None:
                            args.append(product.text)

            elif dict_attr.value:
                items = list(dict_attr.value.items())
            else:
                items = []

            for literal, attr in items:
                # Get the value - handle different attribute types
                attr_value: float | int | str | None = None
                amount_or_percent_attr = attr.find("AmountOrPercent") if hasattr(attr, "find") else None
                if amount_or_percent_attr is not None:
                    # Standard case: attr has AmountOrPercent property
                    val = amount_or_percent_attr()  # pyright: ignore
                    if isinstance(val, float | int | str | None):
                        attr_value = val
                elif hasattr(attr, "__call__"):
                    # Fallback: try calling the attribute directly
                    try:
                        attr_value = attr()
                    except Exception:
                        continue

                # Skip zero or None values
                if attr_value is None or attr_value == 0 or attr_value == 0.0:
                    continue

                formatted_value = self._format_value(attr_value, percental=False)

                literal_struct = buff_struct.find(f"Attributes.{literal}")
                if literal_struct is None:
                    continue

                text_attr = literal_struct.find("Text")
                literal_text = text_attr() if isinstance(text_attr, TextAttribute) else None
                literal_icon = self._get_icon(literal_struct.find("Icon"))

                formatted_texts: list[Text] = []

                if len(args) == 0:
                    if in_additional_effect is True:
                        template_attr = buff_struct.find("AttributeInRange")
                        if isinstance(template_attr, TextAttribute):
                            formatted_texts.append(template_attr().format([literal_text]))
                    elif literal_text:
                        formatted_texts.append(literal_text)
                else:
                    template_attr = buff_struct.find("AttributeFromProvidedNeed")
                    if isinstance(template_attr, TextAttribute):
                        for product in args:
                            formatted_texts.append(template_attr().format([literal_text, product]))

                for formatted_text in formatted_texts:
                    result.append(
                        BuffUI(icon=literal_icon, text=formatted_text, value=formatted_value, literal=literal)
                    )

        except Exception as e:
            logger.debug(f"Failed to create buff UI dict for {property_name}.{attr_name}: {e}")

        if len(result) == 0:
            return None

        return result

    def _create_buff_ui_mesh_graph_upkeep(
        self, property_name: str, attr_name: str, dict_attr: DictAttribute
    ) -> list[BuffUI] | None:
        """Create BuffUI for MeshGraphUpkeep (AreaMaintenanceUpgrade).

        MeshGraphUpkeep is a DictAttribute with dataset literals (Street, Wall, Aqueduct, etc.)
        Each entry has a value representing maintenance cost.

        Args:
            property_name: Property name ("AreaMaintenanceUpgrade")
            attr_name: Attribute name ("MeshGraphUpkeep")
            dict_attr: The MeshGraphUpkeep DictAttribute

        Returns:
            List of BuffUI objects for non-zero values, or None if no buff type found
        """
        try:
            # Step 1: Get buff type name
            buff_type = self.get_buff_type_name(property_name, attr_name)
            if buff_type is None or buff_type not in self.buff_text_structs:
                logger.debug(f"Buff type {buff_type} not found for MeshGraphUpkeep")
                return None

            buff_info = self.buff_text_structs[buff_type]
            buff_struct = buff_info["struct"]

            if not isinstance(buff_struct, DictAttribute):
                logger.debug(f"BuffMeshGraphUpkeep struct is not DictAttribute: {type(buff_struct)}")
                return None

            result: list[BuffUI] = []

            # Step 2: Iterate over dict entries (dataset literals)

            for attr in dict_attr:
                # Get the value - MeshGraphUpkeep has nested dict structure
                # Each entry is like {'UpgradePercent': UpgradePercent: -15}
                literal = attr.name
                attr_value = None

                # Check if attr is a dict with UpgradePercent key
                upgrade_percent_attr = attr.find("UpgradePercent")
                if upgrade_percent_attr is not None:
                    val = upgrade_percent_attr()  # pyright: ignore
                    if isinstance(val, int | float):
                        attr_value = val
                elif hasattr(attr, "__call__"):
                    attr_value = attr()

                # Skip None or zero values
                if attr_value is None or attr_value == 0 or attr_value == 0.0:
                    continue

                # Step 3: Format the value (it's a percentage)
                formatted_value = self._format_value(attr_value, percental=True)

                # Step 4: Get text and icon from buff struct for this literal
                literal_struct = buff_struct.find(f"{literal}")
                if literal_struct is None:
                    continue

                literal_text_attr = literal_struct.find("Text")
                literal_icon_attr = literal_struct.find("Icon")

                literal_text = literal_text_attr() if isinstance(literal_text_attr, TextAttribute) else None
                literal_icon = self._get_icon(literal_icon_attr) if literal_icon_attr else None

                # Step 5: Create BuffUI for this entry
                result.append(BuffUI(icon=literal_icon, text=literal_text, value=formatted_value, literal=literal))

            if len(result) == 0:
                return None

            return result

        except Exception as e:
            logger.debug(f"Failed to create BuffUI for MeshGraphUpkeep: {e}")
            return None

    def _create_buff_ui_replace_workforce(
        self, property_name: str, attr_name: str, dict_attr: DictAttribute
    ) -> list[BuffUI] | None:
        """Create BuffUI for ReplaceWorkforce special case.

        Args:
            property_name: Property name ("MaintenanceUpgrade")
            attr_name: Attribute name ("ReplaceWorkforce")
            dict_attr: The ReplaceWorkforce DictAttribute

        Returns:
            List with single BuffUI object, or None if formatting fails
        """
        try:
            # Step 1: Get buff type name
            buff_type = self.get_buff_type_name(property_name, attr_name)
            if buff_type is None or buff_type not in self.buff_text_structs:
                logger.debug(f"Buff type {buff_type} not found for ReplaceWorkforce")
                return None

            buff_info = self.buff_text_structs[buff_type]

            # Step 2: Format the text with workforce names
            formatted_text = self._format_replace_workforce(dict_attr, buff_info)
            if formatted_text is None:
                logger.debug("Failed to format ReplaceWorkforce text")
                return None

            # Step 3: Get icon from NewWorkforce asset (the replacement workforce)
            icon_obj = None
            try:
                new_workforce_asset = dict_attr.find_ref("NewWorkforce")
                if new_workforce_asset is not None:
                    icon_obj = new_workforce_asset.icon
            except Exception:
                # Icon is optional, continue without it
                pass

            # Step 4: Return single BuffUI object in a list
            return [
                BuffUI(
                    icon=icon_obj,
                    text=formatted_text,
                    value="",  # No numeric value for workforce replacement
                    literal=None,
                )
            ]

        except Exception as e:
            logger.debug(f"Failed to create BuffUI for ReplaceWorkforce: {e}")
            return None

    def create_buff_ui(
        self,
        property_name: str,
        attr_name: str,
        value: float | int | str,
        literal: str | None = None,
        list_item: t.Any = None,
        percental: bool | None = None,
    ) -> BuffUI | None:
        """Create a BuffUI object for an attribute.

        Args:
            property_name: Property name (e.g., "FactoryUpgrade")
            attr_name: Attribute name (e.g., "ProductivityUpgrade")
            value: The attribute value (number or string)
            literal: Optional dataset literal (for DictAttribute)
            list_item: Optional ListItem for formatted text
            percental: Whether the value is a percentage (from UpgradeAttribute)

        Returns:
            BuffUI object or None if no UI text available
        """
        if (
            "Percent" in attr_name
            or "Accuracy" in attr_name
            or attr_name == "BuffTransferSpeedUpgrade"
            or attr_name == "LandTax"
            or attr_name == "PassiveTradeProfitModifier"
        ):
            percental = True

        if attr_name == "BuffReduceCargoImpactUpgrade" or attr_name == "BuffReduceDamageImpactUpgrade":
            percental = True
            value *= -1

        if attr_name == "ActiveTradePriceInPercent" and isinstance(value, int | float):
            value = value - 100

            if value == 0:
                return None

        try:
            # Get buff type name
            buff_type = self.get_buff_type_name(property_name, attr_name)
            if buff_type is None:
                return None

            mapping = self.mappings.get((property_name, attr_name))
            if mapping is None and buff_type in self.buff_text_structs:
                # Try to get from buff text structs
                buff_info = self.buff_text_structs.get(buff_type)
                if buff_info is not None:
                    buff_struct = buff_info["struct"]

                    # Special handling for BuffCanUseTerrain - use terrain-specific text/icon
                    if buff_type == "BuffCanUseTerrain":
                        terrain_type = None
                        if "Forest" in attr_name:
                            terrain_type = "Forest"
                        elif "Meadow" in attr_name:
                            terrain_type = "Meadow"
                        elif "Marsh" in attr_name:
                            terrain_type = "Marsh"

                        if terrain_type:
                            text_attr = buff_struct.find(f"{terrain_type}Text")
                            icon_attr = buff_struct.find(f"{terrain_type}Icon")
                        else:
                            text_attr = buff_struct.find("Text")
                            icon_attr = buff_struct.find("Icon")
                    # Special handling for BuffConstructionSpeed/BuffConstructionCost - use variant text
                    elif buff_type in ["BuffConstructionSpeed", "BuffConstructionCost"]:
                        # Select appropriate variant based on property_name
                        if "Recruitment" in property_name:
                            text_attr = buff_struct.find("RecruitmentText")
                        else:
                            # Default to ShipyardText for other contexts
                            text_attr = buff_struct.find("ShipyardText")
                        icon_attr = buff_struct.find("Icon")
                    else:
                        text_attr = buff_struct.find("Text")
                        icon_attr = buff_struct.find("Icon")

                    text_obj = text_attr() if text_attr is not None else None
                    icon_obj = None

                    if icon_attr is not None:
                        if hasattr(icon_attr, "guid"):
                            # Follow reference to Icon asset
                            icon_asset = icon_attr()
                            if icon_asset is not None:
                                icon_filename = icon_asset.find("Standard.IconFilename") or icon_asset.find(
                                    "IconFilename"
                                )
                                if icon_filename is not None:
                                    icon_obj = icon_filename
                        elif hasattr(icon_attr, "value"):
                            icon_obj = icon_attr

                    mapping = UITextMapping(text=text_obj, icon=icon_obj)

            if mapping is None:
                return None

            # Format value string
            value_str = self._format_value(value, percental=percental)

            # Get formatted text if list_item provided
            formatted_text = None
            if list_item is not None:
                formatted_text = self.format_buff_text(buff_type, list_item)

            return BuffUI(
                icon=mapping.icon,
                text=formatted_text if formatted_text is not None else mapping.text,
                value=value_str,
                literal=literal,
            )

        except Exception as e:
            logger.debug(f"Failed to create BuffUI for {property_name}.{attr_name}: {e}")
            return None

    def _format_value(self, value: float | int | str, percental: bool | None = None) -> str:
        """Format a value as a string with appropriate sign and formatting.

        Args:
            value: The value to format
            percental: Whether to format as percentage (from UpgradeAttribute.percental)

        Returns:
            Formatted string (e.g., "+25%", "50", "-10")
        """
        if isinstance(value, str):
            return value

        # Use percental flag if explicitly provided
        if percental is True:
            # Format as percentage
            # If value is already > 1 or < -1, it's already in percentage form (e.g., 100 = 100%)
            # If value is between -1 and 1, multiply by 100 (e.g., 0.25 = 25%)
            # Otherwise value is already in percentage form
            percent = value * 100 if -1 < value < 1 and value != 0 else value

            if percent == int(percent):
                percent_int = int(percent)
                if percent_int > 0:
                    return f"+{percent_int}%"
                return f"{percent_int}%"
            else:
                if percent > 0:
                    return f"+{percent:.1f}%"
                return f"{percent:.1f}%"
        elif percental is False:
            # Format as regular number
            if value == int(value):
                value_int = int(value)
                if value_int > 0:
                    return f"+{value_int}"
                return str(value_int)
            else:
                if value > 0:
                    return f"+{value:.1f}"
                return f"{value:.1f}"
        else:
            # Auto-detect: if value is between -1 and 1, assume percentage
            if value == int(value):
                # Integer value
                value_int = int(value)
                if value_int > 0:
                    return f"+{value_int}"
                return str(value_int)
            else:
                # Float value - likely a percentage
                percent = value * 100
                if percent == int(percent):
                    percent_int = int(percent)
                    if percent_int > 0:
                        return f"+{percent_int}%"
                    return f"{percent_int}%"
                else:
                    if value > 0:
                        return f"+{percent:.1f}%"
                    return f"{percent:.1f}%"

        return str(value)

    def create_buff_ui_list(self, property_name: str, attr_name: str, list_attr: ListAttribute) -> list[BuffUI] | None:
        """Create BuffUI objects for ListAttribute items.

        This method handles ListAttributes where each item needs formatted text with placeholders.
        For example, FactoryUpgrade.AdditionalOutput items need product name and amount formatting.

        Args:
            property_name: Property name (e.g., "FactoryUpgrade")
            attr_name: Attribute name (e.g., "AdditionalOutput")
            list_attr: The ListAttribute containing the items

        Returns:
            List of BuffUI objects, or None if no valid items
        """
        if list_attr.value is None:
            return None

        result: list[BuffUI] = []

        if attr_name == "AddDeltas":
            return self.format_product_list(list_attr, add_sign=True)

        # Get buff type name
        buff_type = self.get_buff_type_name(property_name, attr_name)
        if buff_type is None or buff_type not in self.buff_text_structs:
            return None

        buff_info = self.buff_text_structs[buff_type]
        buff_struct = buff_info["struct"]

        # Get default icon from buff struct (if available)
        # Note: Some buff types (like BuffResidenceProvidedNeedText) need per-item icons
        default_icon_obj = None
        try:
            # Only try to find Icon if buff_struct is a DictAttribute
            if isinstance(buff_struct, DictAttribute):
                icon_attr = buff_struct.find("Icon")
                default_icon_obj = self._get_icon(icon_attr)
        except Exception:
            # Icon lookup failed, continue without icon
            pass

        for item in list_attr:
            # Format text for this specific item
            formatted_text = self.format_buff_text(buff_type, item)

            if formatted_text is not None:
                # Get item-specific icon for certain buff types
                icon_obj = default_icon_obj
                if buff_type == "BuffResidenceProvidedNeedText":
                    try:
                        # Get icon from the ProvidedNeed asset
                        need_asset = item.find_ref("ProvidedNeed")
                        if need_asset is not None:
                            icon_obj = need_asset.icon
                    except Exception:
                        pass

                value = None
                if attr_name == "RadiusEffectRangeTarget":
                    upgrade = list_attr.parent.RadiusEffectRangeUpgrade  # pyright: ignore
                    if upgrade is not None:
                        val = upgrade()  # pyright: ignore
                        if isinstance(val, int | float | str):
                            value = self._format_value(val, percental=True)

                result.append(
                    BuffUI(
                        icon=icon_obj,
                        text=formatted_text,
                        value=value,  # Value is embedded in formatted text
                    )
                )

        return result if result else None
