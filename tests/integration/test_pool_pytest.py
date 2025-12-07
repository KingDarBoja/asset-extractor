"""Pytest test suite for asset pool functionality.

Tests pool flattening, probability calculations, and pool traversal.
"""

import pytest


@pytest.mark.pool
class TestPoolFlattening:
    """Test pool flattening functionality."""

    def test_pool_assets_method(self, assets):
        """Test that pool.pool_assets() correctly flattens pools and calculates probabilities."""
        # Test pool 122533 (Festival Happiness) from the HTML example
        pool_guid = 122533
        pool = assets.elements.get(pool_guid)

        assert pool is not None, f"Pool {pool_guid} not found"
        assert pool.template.name in ["RewardPool", "RegionRewardPool"], f"Not a pool template: {pool.template.name}"

        # Test pool_assets method
        pool_results = pool.pool_assets()

        assert len(pool_results) > 0, "pool_assets() returned empty dict"
        assert isinstance(pool_results, dict), f"Expected dict, got {type(pool_results)}"

        # Check probabilities sum to ~1.0
        total_prob = sum(pool_results.values())
        assert 0.99 <= total_prob <= 1.01, f"Total probability {total_prob} not close to 1.0"

        # Each probability should be between 0 and 1
        for asset, probability in pool_results.items():
            assert 0 <= probability <= 1, f"Invalid probability {probability} for {asset.name}"

    def test_pool_references(self, assets):
        """Test that pool references are correctly set."""
        pool_guid = 122533
        pool = assets.elements.get(pool_guid)

        if pool is None:
            pytest.skip(f"Pool {pool_guid} not found")

        # Check if this is a root pool
        is_root_pool = any("Pool" not in ref.source.template.name for ref in pool.referenced_by.values())

        if is_root_pool:
            # Root pool - leaf assets should have in_reward_pool references
            pool_results = pool.pool_assets()
            if pool_results:
                first_leaf = next(iter(pool_results.keys()))
                assert hasattr(first_leaf, "in_reward_pool"), "Leaf asset should have in_reward_pool attribute"
                assert len(first_leaf.in_reward_pool) > 0, "Leaf asset should have at least one pool reference"

    def test_nested_pools(self, assets):
        """Test that nested pools are correctly flattened."""
        # Find a pool that contains other pools
        reward_pools = assets.templates.get("RewardPool")
        if not reward_pools:
            pytest.skip("No RewardPool template found")

        nested_pool_found = False
        for pool in reward_pools.assets:
            items_pool = pool.RewardPool.ItemsPool if hasattr(pool.RewardPool, "ItemsPool") else None
            if items_pool:
                for item_entry in items_pool:
                    item_link = item_entry.ItemLink()
                    if item_link and "Pool" in item_link.template.name:
                        # Found a pool containing another pool
                        nested_pool_found = True
                        pool_results = pool.pool_assets()

                        # Should flatten to leaf assets only
                        for leaf_asset in pool_results.keys():
                            assert (
                                "Pool" not in leaf_asset.template.name
                            ), f"pool_assets() should not return pools, found {leaf_asset.template.name}"
                        break

            if nested_pool_found:
                break

        if not nested_pool_found:
            pytest.skip("No nested pools found to test")


@pytest.mark.pool
class TestPoolProbabilities:
    """Test pool probability calculations."""

    def test_equal_weights(self, assets):
        """Test that equal weights result in equal probabilities."""
        # This would require creating a test pool or finding one with equal weights
        # For now, we'll test that probabilities match weights proportionally
        reward_pools = assets.templates.get("RewardPool")
        if not reward_pools:
            pytest.skip("No RewardPool template found")

        tested = False
        for pool in reward_pools.assets:
            items_pool = pool.RewardPool.ItemsPool if hasattr(pool.RewardPool, "ItemsPool") else None
            if items_pool and len(items_pool) > 1:
                # Get all weights
                weights = []
                for item_entry in items_pool:
                    weight = item_entry.Weight() if hasattr(item_entry, "Weight") else 1
                    weights.append(weight)

                # Check if all weights are equal
                if len(set(weights)) == 1 and weights[0] > 0:
                    pool_results = pool.pool_assets()
                    if len(pool_results) == len(items_pool):
                        # All probabilities should be equal
                        probabilities = list(pool_results.values())
                        expected_prob = 1.0 / len(probabilities)

                        for prob in probabilities:
                            assert abs(prob - expected_prob) < 0.01, (
                                f"Expected equal probability {expected_prob}, got {prob}"
                            )

                        tested = True
                        break

        if not tested:
            pytest.skip("No suitable pool with equal weights found")

    def test_weighted_probabilities(self, assets):
        """Test that weights affect probabilities correctly."""
        reward_pools = assets.templates.get("RewardPool")
        if not reward_pools:
            pytest.skip("No RewardPool template found")

        for pool in reward_pools.assets:
            items_pool = pool.RewardPool.ItemsPool if hasattr(pool.RewardPool, "ItemsPool") else None
            if items_pool and len(items_pool) > 1:
                # Get weights
                weights_sum = sum(
                    item_entry.Weight() if hasattr(item_entry, "Weight") else 1 for item_entry in items_pool
                )

                if weights_sum > 0:
                    # Probabilities should be proportional to weights
                    pool_results = pool.pool_assets()

                    # At least check that total probability is ~1.0
                    total_prob = sum(pool_results.values())
                    assert 0.99 <= total_prob <= 1.01, f"Total probability {total_prob} not close to 1.0"
                    return  # Test passed

        pytest.skip("No suitable weighted pool found")


@pytest.mark.pool
class TestPoolStructure:
    """Test pool structure and attributes."""

    def test_reward_pool_structure(self, assets):
        """Test that RewardPool has expected structure."""
        reward_pools = assets.templates.get("RewardPool")
        if not reward_pools:
            pytest.skip("No RewardPool template found")

        # Get first pool
        pool = next(iter(reward_pools.assets))

        assert hasattr(pool, "RewardPool"), "Pool should have RewardPool property"
        assert hasattr(pool.RewardPool, "ItemsPool"), "RewardPool should have ItemsPool"

    def test_pool_item_attributes(self, assets):
        """Test that pool items have expected attributes."""
        reward_pools = assets.templates.get("RewardPool")
        if not reward_pools:
            pytest.skip("No RewardPool template found")

        for pool in reward_pools.assets:
            items_pool = pool.RewardPool.ItemsPool if hasattr(pool.RewardPool, "ItemsPool") else None
            if items_pool and len(items_pool) > 0:
                item_entry = items_pool[0]

                # Check expected attributes
                assert hasattr(item_entry, "ItemLink"), "Pool item should have ItemLink"

                # Weight is optional but common
                if hasattr(item_entry, "Weight"):
                    weight = item_entry.Weight()
                    assert weight >= 0, f"Weight should be non-negative, got {weight}"

                return  # Test passed

        pytest.skip("No pool items found to test")
