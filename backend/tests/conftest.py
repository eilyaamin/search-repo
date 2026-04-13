"""
Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all backend tests.
"""

import pytest
from unittest.mock import Mock
from src.shared.models import Repository, SearchFilters


@pytest.fixture
def sample_repository():
    """Create a sample Repository instance for testing."""
    return Repository(
        id=12345,
        name="test-repo",
        full_name="user/test-repo",
        url="https://github.com/user/test-repo",
        stars=1000,
        forks=200,
        watchers=500,
        open_issues=42,
        language="Python",
        topics=["testing", "python", "github"],
        created_at="2020-01-15T10:30:00Z",
        updated_at="2024-01-15T14:20:00Z",
        score=0.0,
    )


@pytest.fixture
def sample_repositories():
    """Create a list of sample repositories for testing."""
    return [
        Repository(
            id=i,
            name=f"repo{i}",
            full_name=f"user/repo{i}",
            url=f"https://github.com/user/repo{i}",
            stars=100 * i,
            forks=10 * i,
            watchers=5 * i,
            language="Python" if i % 2 == 0 else "JavaScript",
            topics=[f"topic{i}"],
            updated_at="2024-01-01T00:00:00Z",
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def basic_filters():
    """Create basic SearchFilters for testing."""
    return SearchFilters(
        languages=["Python"],
        created_after="2020-01-01",
        page=1,
        per_page=25,
    )


@pytest.fixture
def mock_provider():
    """Create a mock RepositoryProvider for testing."""
    provider = Mock()
    provider.build_query.return_value = "language:Python"
    provider.fetch_repositories.return_value = []
    return provider


@pytest.fixture
def github_api_response():
    """Create a sample GitHub API repository response."""
    return {
        "id": 123456,
        "name": "awesome-project",
        "full_name": "user/awesome-project",
        "html_url": "https://github.com/user/awesome-project",
        "description": "An awesome project",
        "stargazers_count": 5000,
        "forks_count": 800,
        "watchers_count": 5000,
        "open_issues_count": 42,
        "language": "Python",
        "topics": ["machine-learning", "ai", "python"],
        "created_at": "2020-01-15T10:30:00Z",
        "updated_at": "2024-01-15T14:20:00Z",
        "private": False,
        "fork": False,
    }


# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line("markers", "slow: mark test as slow-running")
