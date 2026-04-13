"""
Unit tests for GitHubClient.

Tests the GitHub API client which implements the RepositoryProvider protocol.
"""

import pytest
from unittest.mock import Mock, patch
from src.integrations.github.client import GitHubClient
from src.shared.models import SearchFilters


class TestGitHubClient:
    """Test suite for GitHubClient."""

    def setup_method(self):
        """Setup common test fixtures."""
        self.client = GitHubClient(token="test_token_123")

    def test_initialization_with_token(self):
        """Test client initializes with token."""
        client = GitHubClient(token="my_token")
        assert client.token == "my_token"
        assert "api.github.com" in client.github_url or "github" in client.github_url

    def test_initialization_without_token(self):
        """Test client can initialize without token."""
        client = GitHubClient()
        assert client.token is None

    def test_build_query_delegates_to_service(self):
        """Test build_query delegates to build_github_query function."""
        filters = SearchFilters(languages=["Python"], created_after="2020-01-01")
        
        query = self.client.build_query(filters)
        
        assert "language:Python" in query
        assert "created:>2020-01-01" in query

    def test_build_query_with_no_filters(self):
        """Test build_query with empty filters."""
        filters = SearchFilters()
        
        query = self.client.build_query(filters)
        
        # Should return fallback query
        assert query == "stars:>0"

    def test_build_query_with_multiple_languages(self):
        """Test build_query with multiple languages."""
        filters = SearchFilters(languages=["Python", "JavaScript", "Go"])
        
        query = self.client.build_query(filters)
        
        assert "language:Python" in query
        assert "language:JavaScript" in query
        assert "language:Go" in query

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_calls_search_with_correct_params(self, mock_search):
        """Test fetch_repositories calls search_repositories correctly."""
        # Setup
        mock_search.return_value = [{"id": 1}, {"id": 2}]
        
        # Execute
        result = self.client.fetch_repositories("language:Python", page=2)
        
        # Verify
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["query"] == "language:Python"
        assert call_kwargs["page"] == 2
        assert call_kwargs["token"] == "test_token_123"
        assert "per_page" in call_kwargs
        
    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_returns_results(self, mock_search):
        """Test fetch_repositories returns repository list."""
        # Setup
        expected = [{"id": 1, "name": "repo1"}, {"id": 2, "name": "repo2"}]
        mock_search.return_value = expected
        
        # Execute
        result = self.client.fetch_repositories("language:Python", page=1)
        
        # Verify
        assert result == expected

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_empty_results(self, mock_search):
        """Test fetch_repositories handles empty results."""
        # Setup
        mock_search.return_value = []
        
        # Execute
        result = self.client.fetch_repositories("language:UnknownLang", page=1)
        
        # Verify
        assert result == []

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_handles_422_api_limit(self, mock_search):
        """Test fetch_repositories handles GitHub's 1000 result limit (422)."""
        # Setup
        error = Exception("Validation Failed")
        error.status_code = 422
        mock_search.side_effect = error
        
        # Execute
        result = self.client.fetch_repositories("language:Python", page=11)
        
        # Verify - should return empty list instead of raising
        assert result == []

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_handles_403_rate_limit(self, mock_search):
        """Test fetch_repositories raises on 403 rate limit."""
        # Setup
        error = Exception("Rate limit exceeded")
        error.status_code = 403
        mock_search.side_effect = error
        
        # Execute & Verify
        with pytest.raises(Exception):
            self.client.fetch_repositories("language:Python", page=1)

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_raises_on_other_errors(self, mock_search):
        """Test fetch_repositories raises on other errors."""
        # Setup
        mock_search.side_effect = Exception("Network error")
        
        # Execute & Verify
        with pytest.raises(Exception):
            self.client.fetch_repositories("language:Python", page=1)

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_passes_token_to_search(self, mock_search):
        """Test fetch_repositories passes token for authentication."""
        # Setup
        mock_search.return_value = []
        client_with_token = GitHubClient(token="my_secret_token")
        
        # Execute
        client_with_token.fetch_repositories("language:Python", page=1)
        
        # Verify token was passed
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["token"] == "my_secret_token"

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_without_token(self, mock_search):
        """Test fetch_repositories works without token (lower rate limit)."""
        # Setup
        mock_search.return_value = [{"id": 1}]
        client_no_token = GitHubClient()
        
        # Execute
        result = client_no_token.fetch_repositories("language:Python", page=1)
        
        # Verify
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["token"] is None
        assert len(result) == 1

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_uses_config_page_size(self, mock_search):
        """Test fetch_repositories uses configured page size."""
        # Setup
        mock_search.return_value = []
        
        # Execute
        self.client.fetch_repositories("language:Python", page=1)
        
        # Verify per_page is set from Config.GITHUB_CHUNK_SIZE
        call_kwargs = mock_search.call_args[1]
        assert "per_page" in call_kwargs
        # Should match Config.GITHUB_CHUNK_SIZE (default 100)
        assert call_kwargs["per_page"] == 100

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_different_pages(self, mock_search):
        """Test fetch_repositories works for different page numbers."""
        # Setup
        mock_search.return_value = []
        
        # Execute
        for page in [1, 5, 10]:
            self.client.fetch_repositories("language:Python", page=page)
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs["page"] == page

    @patch("src.integrations.github.client.search_repositories")
    def test_fetch_repositories_complex_query(self, mock_search):
        """Test fetch_repositories with complex query string."""
        # Setup
        mock_search.return_value = []
        complex_query = "language:Python language:JavaScript created:>2020-01-01 stars:>100"
        
        # Execute
        self.client.fetch_repositories(complex_query, page=1)
        
        # Verify
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["query"] == complex_query
