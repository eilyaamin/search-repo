"""
Unit tests for RepositoryService.

Tests the application service which orchestrates repository search,
scoring, sorting, and UI pagination.
"""

import pytest
from unittest.mock import Mock
from dataclasses import asdict
from src.features.repositories.service import RepositoryService
from src.shared.models import SearchFilters, Repository, PaginationMetadata


def dummy_scoring_fn(repo: Repository) -> float:
    """Simple scoring function for testing - scores by stars."""
    return float(repo.stars)


class TestRepositoryService:
    """Test suite for RepositoryService."""

    def setup_method(self):
        """Setup common test fixtures."""
        self.mock_data_service = Mock()
        self.service = RepositoryService(
            data_service=self.mock_data_service, scoring_fn=dummy_scoring_fn
        )

    def test_initialization(self):
        """Test service initializes with dependencies."""
        assert self.service.data_service == self.mock_data_service
        assert self.service.scoring_fn == dummy_scoring_fn

    def test_fetch_and_rank_basic_workflow(self):
        """Test basic workflow: fetch, score, sort, paginate."""
        # Setup
        filters = SearchFilters(languages=["Python"], page=1, per_page=25)
        mock_repos = [
            Repository(
                id=1,
                name="repo1",
                full_name="user/repo1",
                url="https://github.com/user/repo1",
                stars=100,
            ),
            Repository(
                id=2,
                name="repo2",
                full_name="user/repo2",
                url="https://github.com/user/repo2",
                stars=200,
            ),
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify
        self.mock_data_service.get_repositories.assert_called_once_with(filters)
        assert len(result_dicts) == 2
        assert isinstance(metadata, dict)
        # Results should be sorted by score (stars) descending
        assert result_dicts[0]["stars"] == 200  # Higher stars first
        assert result_dicts[1]["stars"] == 100

    def test_scoring_applied_to_all_repos(self):
        """Test scoring function is applied to all repositories."""
        # Setup
        filters = SearchFilters(page=1, per_page=25)
        mock_repos = [
            Repository(id=i, name=f"repo{i}", full_name=f"user/repo{i}", 
                      url=f"url{i}", stars=i * 10)
            for i in range(1, 6)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, _ = self.service.fetch_and_rank_repositories(filters)

        # Verify all repos have scores
        for repo_dict in result_dicts:
            assert "score" in repo_dict
            assert repo_dict["score"] > 0

    def test_sorting_by_score_descending(self):
        """Test repositories are sorted by score (highest first)."""
        # Setup
        filters = SearchFilters(page=1, per_page=25)
        mock_repos = [
            Repository(id=1, name="low", full_name="u/low", url="url", stars=10),
            Repository(id=2, name="high", full_name="u/high", url="url", stars=100),
            Repository(id=3, name="medium", full_name="u/medium", url="url", stars=50),
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, _ = self.service.fetch_and_rank_repositories(filters)

        # Verify sorted descending by score (stars in our test)
        assert result_dicts[0]["stars"] == 100
        assert result_dicts[1]["stars"] == 50
        assert result_dicts[2]["stars"] == 10

    def test_pagination_first_page(self):
        """Test pagination returns correct first page."""
        # Setup
        filters = SearchFilters(page=1, per_page=2)
        mock_repos = [
            Repository(id=i, name=f"repo{i}", full_name=f"u/repo{i}", 
                      url="url", stars=100-i)
            for i in range(5)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify - should get 2 items (per_page=2)
        assert len(result_dicts) == 2
        assert metadata["current_page"] == 1
        assert metadata["per_page"] == 2
        assert metadata["has_next"] is True
        assert metadata["has_previous"] is False

    def test_pagination_middle_page(self):
        """Test pagination returns correct middle page."""
        # Setup
        filters = SearchFilters(page=2, per_page=2)
        mock_repos = [
            Repository(id=i, name=f"repo{i}", full_name=f"u/repo{i}",
                      url="url", stars=100-i)
            for i in range(5)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify
        assert len(result_dicts) == 2
        assert metadata["current_page"] == 2
        assert metadata["has_next"] is True
        assert metadata["has_previous"] is True

    def test_pagination_last_partial_page(self):
        """Test pagination handles partial last page correctly."""
        # Setup
        filters = SearchFilters(page=3, per_page=2)
        mock_repos = [
            Repository(id=i, name=f"repo{i}", full_name=f"u/repo{i}",
                      url="url", stars=100-i)
            for i in range(5)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify - should get 1 item (only 1 left)
        assert len(result_dicts) == 1
        assert metadata["current_page"] == 3
        assert metadata["has_next"] is False
        assert metadata["has_previous"] is True

    def test_pagination_beyond_available_pages(self):
        """Test requesting page beyond available data."""
        # Setup
        filters = SearchFilters(page=10, per_page=25)
        mock_repos = [
            Repository(id=1, name="repo1", full_name="u/repo1", url="url", stars=100)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify - should get empty list
        assert len(result_dicts) == 0
        assert metadata["has_next"] is False

    def test_empty_results_handled(self):
        """Test service handles empty results from data service."""
        # Setup
        filters = SearchFilters(page=1, per_page=25)
        self.mock_data_service.get_repositories.return_value = []

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify
        assert len(result_dicts) == 0
        assert metadata["has_next"] is False
        assert metadata["has_previous"] is False

    def test_has_next_logic(self):
        """Test has_next is True only when full page returned."""
        filters = SearchFilters(page=1, per_page=3)

        # Test with exactly per_page items
        self.mock_data_service.get_repositories.return_value = [
            Repository(id=i, name=f"repo{i}", full_name=f"u/repo{i}",
                      url="url", stars=100)
            for i in range(3)
        ]
        _, metadata = self.service.fetch_and_rank_repositories(filters)
        assert metadata["has_next"] is True

        # Test with fewer than per_page items
        self.mock_data_service.get_repositories.return_value = [
            Repository(id=1, name="repo1", full_name="u/repo1", url="url", stars=100)
        ]
        _, metadata = self.service.fetch_and_rank_repositories(filters)
        assert metadata["has_next"] is False

    def test_has_previous_logic(self):
        """Test has_previous is based on page number."""
        # Page 1
        filters = SearchFilters(page=1, per_page=25)
        self.mock_data_service.get_repositories.return_value = []
        _, metadata = self.service.fetch_and_rank_repositories(filters)
        assert metadata["has_previous"] is False

        # Page 2
        filters = SearchFilters(page=2, per_page=25)
        _, metadata = self.service.fetch_and_rank_repositories(filters)
        assert metadata["has_previous"] is True

    def test_returns_dicts_not_objects(self):
        """Test service returns dictionaries, not Repository objects."""
        # Setup
        filters = SearchFilters(page=1, per_page=25)
        self.mock_data_service.get_repositories.return_value = [
            Repository(id=1, name="repo1", full_name="u/repo1", url="url", stars=100)
        ]

        # Execute
        result_dicts, _ = self.service.fetch_and_rank_repositories(filters)

        # Verify
        assert isinstance(result_dicts[0], dict)
        assert "id" in result_dicts[0]
        assert "name" in result_dicts[0]
        assert "score" in result_dicts[0]

    def test_custom_scoring_function(self):
        """Test service works with custom scoring functions."""
        # Custom scorer that uses forks instead of stars
        def fork_scorer(repo: Repository) -> float:
            return float(repo.forks)

        service = RepositoryService(
            data_service=self.mock_data_service, scoring_fn=fork_scorer
        )

        filters = SearchFilters(page=1, per_page=25)
        mock_repos = [
            Repository(id=1, name="r1", full_name="u/r1", url="url", 
                      stars=100, forks=5),
            Repository(id=2, name="r2", full_name="u/r2", url="url",
                      stars=50, forks=20),
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        result_dicts, _ = service.fetch_and_rank_repositories(filters)

        # Should be sorted by forks, not stars
        assert result_dicts[0]["forks"] == 20  # Higher forks first
        assert result_dicts[1]["forks"] == 5

    def test_large_dataset_pagination(self):
        """Test pagination with large dataset."""
        # Setup
        filters = SearchFilters(page=5, per_page=25)
        mock_repos = [
            Repository(id=i, name=f"repo{i}", full_name=f"u/repo{i}",
                      url="url", stars=1000-i)
            for i in range(200)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        # Execute
        result_dicts, metadata = self.service.fetch_and_rank_repositories(filters)

        # Verify
        assert len(result_dicts) == 25
        assert metadata["current_page"] == 5
        # Page 5 means: (5-1)*25 = 100 to 125
        # After sorting by stars descending, these would be items 100-124

    def test_metadata_structure(self):
        """Test pagination metadata has correct structure."""
        filters = SearchFilters(page=2, per_page=10)
        self.mock_data_service.get_repositories.return_value = [
            Repository(id=1, name="r", full_name="u/r", url="url", stars=100)
        ]

        _, metadata = self.service.fetch_and_rank_repositories(filters)

        assert "current_page" in metadata
        assert "per_page" in metadata
        assert "has_next" in metadata
        assert "has_previous" in metadata
        assert metadata["current_page"] == 2
        assert metadata["per_page"] == 10

    def test_score_persists_in_output(self):
        """Test calculated scores are included in output."""
        filters = SearchFilters(page=1, per_page=25)
        mock_repos = [
            Repository(id=1, name="repo1", full_name="u/repo1", url="url", stars=150)
        ]
        self.mock_data_service.get_repositories.return_value = mock_repos

        result_dicts, _ = self.service.fetch_and_rank_repositories(filters)

        assert "score" in result_dicts[0]
        assert result_dicts[0]["score"] == 150.0  # Our dummy scorer uses stars

    def test_filters_passed_to_data_service(self):
        """Test filters are passed correctly to data service."""
        filters = SearchFilters(
            languages=["Python", "JavaScript"],
            created_after="2020-01-01",
            page=3,
            per_page=50,
        )
        self.mock_data_service.get_repositories.return_value = []

        self.service.fetch_and_rank_repositories(filters)

        self.mock_data_service.get_repositories.assert_called_once_with(filters)
