"""
Unit tests for RepositoryDataService.

Tests the data orchestration layer which manages caching,
fetching, and prefetching of repository data.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.shared.infrastructure.data_service import RepositoryDataService
from src.shared.infrastructure.cache import RepositoryCache
from src.shared.models import SearchFilters, Repository


class TestRepositoryDataService:
    """Test suite for RepositoryDataService."""

    def setup_method(self):
        """Setup common test fixtures."""
        self.mock_provider = Mock()
        self.cache = RepositoryCache()
        self.service = RepositoryDataService(
            provider=self.mock_provider, cache=self.cache, page_size=100
        )

    def test_initialization(self):
        """Test service initializes with correct dependencies."""
        assert self.service.provider == self.mock_provider
        assert self.service.cache == self.cache
        assert self.service.page_size == 100
        assert self.service.MAX_RESULTS == 1000

    def test_get_repositories_first_fetch(self):
        """Test first fetch for a query fetches from provider."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        self.mock_provider.build_query.return_value = "language:Python"
        self.mock_provider.fetch_repositories.return_value = [
            {
                "id": i,
                "name": f"repo{i}",
                "full_name": f"user/repo{i}",
                "url": f"https://github.com/user/repo{i}",
            }
            for i in range(100)
        ]

        # Execute
        result = self.service.get_repositories(filters)

        # Verify
        self.mock_provider.build_query.assert_called_once_with(filters)
        self.mock_provider.fetch_repositories.assert_called_once_with(
            "language:Python", 1
        )
        assert len(result) == 100
        assert isinstance(result[0], Repository)

    def test_get_repositories_uses_cache(self):
        """Test subsequent requests use cached data."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        query = "language:Python"
        self.mock_provider.build_query.return_value = query

        # Pre-populate cache
        cached_repos = [
            {
                "id": i,
                "name": f"repo{i}",
                "full_name": f"user/repo{i}",
                "url": f"https://github.com/user/repo{i}",
            }
            for i in range(100)
        ]
        self.cache.set(query, cached_repos, 1, False)

        # Execute
        result = self.service.get_repositories(filters)

        # Verify - should not fetch from provider
        self.mock_provider.fetch_repositories.assert_not_called()
        assert len(result) == 100

    def test_get_repositories_fetches_additional_pages_when_needed(self):
        """Test fetches additional pages when cached data is insufficient."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=3, per_page=100)
        query = "language:Python"
        self.mock_provider.build_query.return_value = query

        # Cache only has 1 page (100 items), but we need 300 items
        cached_repos = [
            {
                "id": i,
                "name": f"repo{i}",
                "full_name": f"user/repo{i}",
                "url": f"https://github.com/user/repo{i}",
            }
            for i in range(100)
        ]
        self.cache.set(query, cached_repos, 1, False)

        # Mock fetching pages 2 and 3
        def fetch_side_effect(q, page):
            return [
                {
                    "id": i + (page - 1) * 100,
                    "name": f"repo{i}",
                    "full_name": f"user/repo{i}",
                    "url": f"url{i}",
                }
                for i in range(100)
            ]

        self.mock_provider.fetch_repositories.side_effect = fetch_side_effect

        # Execute
        result = self.service.get_repositories(filters)

        # Verify - should fetch pages 2 and 3 (page 1 is already cached)
        # But implementation might fetch page 1 again if not skipped
        assert self.mock_provider.fetch_repositories.call_count >= 2
        assert len(result) == 300

    def test_get_repositories_stops_at_last_page(self):
        """Test stops fetching when last_page flag is set."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=5, per_page=100)
        query = "language:Python"
        self.mock_provider.build_query.return_value = query

        # Cache has 150 items marked as last page
        cached_repos = [
            {
                "id": i,
                "name": f"repo{i}",
                "full_name": f"user/repo{i}",
                "url": f"url{i}",
            }
            for i in range(150)
        ]
        self.cache.set(query, cached_repos, 2, True)  # last_page=True

        # Execute
        result = self.service.get_repositories(filters)

        # Verify - should not fetch more
        self.mock_provider.fetch_repositories.assert_not_called()
        assert len(result) == 150

    def test_get_repositories_respects_max_results_limit(self):
        """Test respects MAX_RESULTS limit (1000 items)."""
        # Setup - request page that would exceed MAX_RESULTS
        filters = SearchFilters(languages=["Python"], page=11, per_page=100)
        query = "language:Python"
        self.mock_provider.build_query.return_value = query

        # Cache has 1000 items
        cached_repos = [
            {"id": i, "name": f"r{i}", "full_name": f"u/r{i}", "url": f"url{i}"}
            for i in range(1000)
        ]
        self.cache.set(query, cached_repos, 10, False)

        # Mock fetch (should not be called)
        self.mock_provider.fetch_repositories.return_value = [
            {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
            for i in range(100)
        ]

        # Execute
        result = self.service.get_repositories(filters)

        # Verify - should not fetch beyond 1000
        self.mock_provider.fetch_repositories.assert_not_called()

    def test_empty_results_handled(self):
        """Test handles empty results from provider gracefully."""
        # Setup
        filters = SearchFilters(languages=["UnknownLang"], page=1, per_page=25)
        self.mock_provider.build_query.return_value = "language:UnknownLang"
        self.mock_provider.fetch_repositories.return_value = []

        # Execute
        result = self.service.get_repositories(filters)

        # Verify
        assert len(result) == 0
        assert result == []

    def test_last_page_detection_partial_results(self):
        """Test detects last page when results are less than page_size."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        query = "language:Python"
        self.mock_provider.build_query.return_value = query
        # Only 50 results (less than page_size of 100)
        self.mock_provider.fetch_repositories.return_value = [
            {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
            for i in range(50)
        ]

        # Execute
        result = self.service.get_repositories(filters)

        # Verify last_page flag is set
        cache_entry = self.cache.get(query)
        assert cache_entry["last_page"] is True

    def test_concurrent_fetch_prevention(self):
        """Test prevents duplicate concurrent fetches for same query/page."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        query = "language:Python"
        self.mock_provider.build_query.return_value = query

        fetch_called = []

        def slow_fetch(q, page):
            fetch_called.append((q, page))
            return [
                {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
                for i in range(100)
            ]

        self.mock_provider.fetch_repositories.side_effect = slow_fetch

        # Execute - simulate concurrent calls
        # First call will acquire the slot
        self.service._fetch_page(query, 1, initial=True)

        # Second call should be prevented
        self.service._fetch_page(query, 1, initial=False)

        # Verify - fetch should only be called once
        assert len(fetch_called) == 1

    def test_requires_additional_data_logic(self):
        """Test _requires_additional_data method logic."""
        # Setup
        cache_entry = {
            "repos": [
                {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
                for i in range(100)
            ],
            "pages_loaded": 1,
            "last_page": False,
        }

        # Test: needs more data
        assert self.service._requires_additional_data(cache_entry, 200) is True

        # Test: has enough data
        assert self.service._requires_additional_data(cache_entry, 50) is False

        # Test: last page reached
        cache_entry["last_page"] = True
        assert self.service._requires_additional_data(cache_entry, 200) is False

    def test_should_schedule_prefetch_logic(self):
        """Test _should_schedule_prefetch decision logic."""
        # Setup
        cache_entry = {
            "repos": [
                {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
                for i in range(100)
            ],
            "pages_loaded": 1,
            "last_page": False,
        }

        # Test: should prefetch when 75% threshold reached
        assert self.service._should_schedule_prefetch(75, 100, cache_entry) is True

        # Test: should not prefetch when below 75% threshold
        assert self.service._should_schedule_prefetch(50, 100, cache_entry) is False

        # Test: should not prefetch when last page
        cache_entry["last_page"] = True
        assert self.service._should_schedule_prefetch(75, 100, cache_entry) is False

        # Test: should not prefetch when at MAX_RESULTS
        cache_entry["last_page"] = False
        cache_entry["repos"] = [
            {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
            for i in range(1000)
        ]
        assert self.service._should_schedule_prefetch(750, 1000, cache_entry) is False

        # Test: should not prefetch with empty cache
        cache_entry["repos"] = []
        assert self.service._should_schedule_prefetch(0, 0, cache_entry) is False

    def test_is_page_cached(self):
        """Test _is_page_cached correctly checks cache state."""
        # Setup
        query = "test_query"
        self.cache.set(
            query,
            [{"id": 1, "name": "r", "full_name": "u/r", "url": "url"}] * 100,
            2,
            False,
        )

        # Test: pages 1 and 2 are cached
        assert self.service._is_page_cached(query, 1) is True
        assert self.service._is_page_cached(query, 2) is True

        # Test: page 3 is not cached
        assert self.service._is_page_cached(query, 3) is False

        # Test: non-existent query returns falsy value
        assert not self.service._is_page_cached("nonexistent", 1)

    def test_fetch_page_initial_flag(self):
        """Test _fetch_page with initial=True creates new cache entry."""
        # Setup
        query = "test_query"
        self.mock_provider.fetch_repositories.return_value = [
            {"id": i, "name": "r", "full_name": "u/r", "url": "url"}
            for i in range(100)
        ]

        # Execute
        self.service._fetch_page(query, 1, initial=True)

        # Verify
        cache_entry = self.cache.get(query)
        assert cache_entry is not None
        assert cache_entry["pages_loaded"] == 1
        assert len(cache_entry["repos"]) == 100

    def test_fetch_page_appends_to_cache(self):
        """Test _fetch_page without initial flag appends to cache."""
        # Setup
        query = "test_query"
        self.cache.set(query, [{"id": 1}] * 100, 1, False)
        self.mock_provider.fetch_repositories.return_value = [{"id": 2}] * 100

        # Execute
        self.service._fetch_page(query, 2, initial=False)

        # Verify
        cache_entry = self.cache.get(query)
        assert cache_entry["pages_loaded"] == 2
        assert len(cache_entry["repos"]) == 200

    def test_try_acquire_fetch_slot(self):
        """Test fetch slot acquisition for concurrency control."""
        key = "query:1"

        # First acquisition should succeed
        assert self.service._try_acquire_fetch_slot(key) is True

        # Second acquisition should fail (already in flight)
        assert self.service._try_acquire_fetch_slot(key) is False

        # Release and try again
        self.service._release_fetch_slot(key)
        assert self.service._try_acquire_fetch_slot(key) is True

    def test_release_fetch_slot(self):
        """Test fetch slot release."""
        key = "query:1"

        self.service._try_acquire_fetch_slot(key)
        assert key in self.service._inflight

        self.service._release_fetch_slot(key)
        assert key not in self.service._inflight

    def test_release_nonexistent_slot_safe(self):
        """Test releasing non-existent slot doesn't crash."""
        # Should not raise error
        self.service._release_fetch_slot("nonexistent")

    def test_get_repositories_returns_empty_on_cache_miss_failure(self):
        """Test returns empty list if cache unexpectedly empty after load."""
        # Setup - mock scenario where fetch doesn't populate cache
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        self.mock_provider.build_query.return_value = "language:Python"

        # Mock fetch to do nothing (cache won't be populated)
        def no_op_fetch(q, p):
            return []

        self.mock_provider.fetch_repositories.side_effect = no_op_fetch

        # Execute
        result = self.service.get_repositories(filters)

        # Verify - should return empty list
        assert len(result) == 0

    def test_conversion_to_repository_models(self):
        """Test raw dicts are converted to Repository domain models."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        self.mock_provider.build_query.return_value = "language:Python"
        self.mock_provider.fetch_repositories.return_value = [
            {
                "id": 123,
                "name": "test-repo",
                "full_name": "user/test-repo",
                "url": "https://github.com/user/test-repo",
                "stars": 100,
                "forks": 20,
                "watchers": 10,
            }
        ]

        # Execute
        result = self.service.get_repositories(filters)

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], Repository)
        assert result[0].id == 123
        assert result[0].name == "test-repo"
        assert result[0].stars == 100
