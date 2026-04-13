"""
Unit tests for pagination utilities.

Tests the paginate function which slices lists into pages.
"""

import pytest
from src.shared.utils.pagination import paginate


class TestPaginate:
    """Test suite for pagination utility function."""

    def test_first_page_of_items(self):
        """Test getting the first page of items."""
        items = list(range(1, 101))  # 1-100
        result = paginate(items, page=1, per_page=10)

        assert len(result) == 10
        assert result == list(range(1, 11))

    def test_middle_page_of_items(self):
        """Test getting a middle page of items."""
        items = list(range(1, 101))  # 1-100
        result = paginate(items, page=5, per_page=10)

        assert len(result) == 10
        assert result == list(range(41, 51))

    def test_last_full_page(self):
        """Test getting the last full page when items divide evenly."""
        items = list(range(1, 101))  # 1-100
        result = paginate(items, page=10, per_page=10)

        assert len(result) == 10
        assert result == list(range(91, 101))

    def test_partial_last_page(self):
        """Test getting a partial last page."""
        items = list(range(1, 26))  # 1-25
        result = paginate(items, page=3, per_page=10)

        assert len(result) == 5
        assert result == list(range(21, 26))

    def test_page_beyond_available_returns_empty(self):
        """Test requesting page beyond available items returns empty list."""
        items = list(range(1, 11))  # 1-10
        result = paginate(items, page=5, per_page=10)

        assert len(result) == 0
        assert result == []

    def test_empty_list_returns_empty(self):
        """Test paginating empty list returns empty list."""
        items = []
        result = paginate(items, page=1, per_page=10)

        assert len(result) == 0
        assert result == []

    def test_single_item(self):
        """Test paginating a single item."""
        items = [42]
        result = paginate(items, page=1, per_page=10)

        assert len(result) == 1
        assert result == [42]

    def test_per_page_larger_than_items(self):
        """Test per_page larger than total items returns all items."""
        items = list(range(1, 6))  # 1-5
        result = paginate(items, page=1, per_page=100)

        assert len(result) == 5
        assert result == list(range(1, 6))

    def test_per_page_of_one(self):
        """Test pagination with one item per page."""
        items = list(range(1, 11))  # 1-10
        result = paginate(items, page=3, per_page=1)

        assert len(result) == 1
        assert result == [3]

    def test_page_zero_treated_as_page_one(self):
        """Test page 0 is normalized to page 1."""
        items = list(range(1, 21))  # 1-20
        result = paginate(items, page=0, per_page=10)

        assert len(result) == 10
        assert result == list(range(1, 11))

    def test_negative_page_treated_as_page_one(self):
        """Test negative page is normalized to page 1."""
        items = list(range(1, 21))  # 1-20
        result = paginate(items, page=-5, per_page=10)

        assert len(result) == 10
        assert result == list(range(1, 11))

    def test_per_page_zero_treated_as_one(self):
        """Test per_page of 0 is normalized to 1."""
        items = list(range(1, 11))  # 1-10
        result = paginate(items, page=2, per_page=0)

        assert len(result) == 1
        assert result == [2]

    def test_negative_per_page_treated_as_one(self):
        """Test negative per_page is normalized to 1."""
        items = list(range(1, 11))  # 1-10
        result = paginate(items, page=3, per_page=-10)

        assert len(result) == 1
        assert result == [3]

    def test_preserves_item_type_and_order(self):
        """Test pagination preserves item types and order."""
        items = ["a", "b", "c", "d", "e", "f", "g", "h"]
        result = paginate(items, page=2, per_page=3)

        assert result == ["d", "e", "f"]
        assert all(isinstance(item, str) for item in result)

    def test_with_dictionaries(self):
        """Test pagination works with dictionary items."""
        items = [{"id": i, "value": i * 10} for i in range(1, 21)]
        result = paginate(items, page=2, per_page=5)

        assert len(result) == 5
        assert result[0] == {"id": 6, "value": 60}
        assert result[4] == {"id": 10, "value": 100}

    def test_large_page_number(self):
        """Test pagination with very large page number."""
        items = list(range(1, 11))  # 1-10
        result = paginate(items, page=1000, per_page=5)

        assert len(result) == 0
        assert result == []

    def test_exact_division_boundary(self):
        """Test pagination at exact division boundaries."""
        items = list(range(1, 51))  # 1-50
        
        # Test last item of page 2
        page2 = paginate(items, page=2, per_page=25)
        assert page2[-1] == 50
        
        # Test first item of page 2
        assert page2[0] == 26

    def test_real_world_scenario_25_per_page(self):
        """Test realistic scenario with 25 items per page."""
        # Simulate 137 repositories
        items = [{"id": i, "name": f"repo-{i}"} for i in range(1, 138)]
        
        # Page 1: items 1-25
        page1 = paginate(items, page=1, per_page=25)
        assert len(page1) == 25
        assert page1[0]["id"] == 1
        assert page1[24]["id"] == 25
        
        # Page 3: items 51-75
        page3 = paginate(items, page=3, per_page=25)
        assert len(page3) == 25
        assert page3[0]["id"] == 51
        
        # Page 6: items 126-137 (partial)
        page6 = paginate(items, page=6, per_page=25)
        assert len(page6) == 12
        assert page6[0]["id"] == 126
        assert page6[-1]["id"] == 137
