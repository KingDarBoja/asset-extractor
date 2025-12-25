"""Quest tracking and traversal utilities."""

from assetextractor.parsing.core.assets import Asset, AssetCache
from assetextractor.parsing.core.texts import TextCache


class QuestTracker:
    """Handle quest discovery and traversal."""

    def __init__(self, assets: AssetCache, texts: TextCache):
        """Initialize the quest tracker.

        Args:
            assets: Asset cache for looking up assets
            texts: Text cache for localized text
        """
        self.assets = assets
        self.texts = texts

    def find_quest(self, start_asset: Asset, max_depth: int = 10) -> Asset | None:
        """Find parent quest for any asset type.

        Traverses upward through the asset reference chain to find a Quest asset.
        Handles direct LinkedQuestEntry references and reference chain traversal.

        Args:
            start_asset: The asset to start searching from
            max_depth: Maximum depth to traverse

        Returns:
            Quest asset if found, None otherwise
        """
        visited: set[int] = set()
        return self._traverse_to_quest(start_asset, visited, max_depth)

    def _traverse_to_quest(self, start_asset: Asset, visited: set[int], max_depth: int) -> Asset | None:
        """Traverse upward through references to find a quest.

        Args:
            start_asset: The asset to start searching from
            visited: Set of visited asset GUIDs to prevent cycles
            max_depth: Maximum depth to traverse

        Returns:
            Quest asset if found, None otherwise
        """
        current = start_asset
        depth = 0

        while depth < max_depth:
            # Check if current asset is a quest
            if self.is_quest_template(current.template.name):
                return current

            # Check for direct LinkedQuestEntry reference
            linked_quest = current.find_ref("Objective.Objective.ConditionQuestObjective.LinkedQuestEntry")
            if linked_quest is not None:
                return linked_quest

            # Find next asset in chain by traversing referenced_by
            found_next = False
            if hasattr(current, "referenced_by"):
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

    @staticmethod
    def is_quest_template(template_name: str) -> bool:
        """Check if a template name represents a Quest.

        Args:
            template_name: The template name to check

        Returns:
            True if this is a Quest template
        """
        return template_name == "Quest" or ("Quest" in template_name and "Component" not in template_name)
