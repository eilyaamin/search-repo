"""
Unit tests for GitHub DTO transformations.

Tests the from_github_api function which transforms GitHub API responses
into internal Repository domain models.
"""

import pytest
from src.integrations.github.dto import from_github_api
from src.shared.models import Repository


class TestFromGitHubAPI:
    """Test suite for GitHub API to domain model transformation."""

    def test_complete_repository_transformation(self):
        """Test transformation with all fields present."""
        github_repo = {
            "id": 123456,
            "name": "awesome-project",
            "full_name": "user/awesome-project",
            "html_url": "https://github.com/user/awesome-project",
            "stargazers_count": 5000,
            "forks_count": 800,
            "watchers_count": 5000,
            "open_issues_count": 42,
            "language": "Python",
            "topics": ["machine-learning", "ai", "python"],
            "created_at": "2020-01-15T10:30:00Z",
            "updated_at": "2024-01-15T14:20:00Z",
        }

        result = from_github_api(github_repo)

        assert isinstance(result, Repository)
        assert result.id == 123456
        assert result.name == "awesome-project"
        assert result.full_name == "user/awesome-project"
        assert result.url == "https://github.com/user/awesome-project"
        assert result.stars == 5000
        assert result.forks == 800
        assert result.watchers == 5000
        assert result.open_issues == 42
        assert result.language == "Python"
        assert result.topics == ["machine-learning", "ai", "python"]
        assert result.created_at == "2020-01-15T10:30:00Z"
        assert result.updated_at == "2024-01-15T14:20:00Z"

    def test_missing_optional_fields_use_defaults(self):
        """Test transformation with missing optional fields."""
        github_repo = {
            "id": 789,
            "name": "minimal-repo",
            "full_name": "user/minimal-repo",
        }

        result = from_github_api(github_repo)

        assert result.id == 789
        assert result.name == "minimal-repo"
        assert result.full_name == "user/minimal-repo"
        assert result.url == ""  # Missing html_url
        assert result.stars == 0
        assert result.forks == 0
        assert result.watchers == 0
        assert result.open_issues == 0
        assert result.language is None
        assert result.topics == []
        assert result.created_at is None
        assert result.updated_at is None

    def test_null_language_handled(self):
        """Test repository with null language (no primary language detected)."""
        github_repo = {
            "id": 111,
            "name": "no-language-repo",
            "full_name": "user/no-language-repo",
            "language": None,
        }

        result = from_github_api(github_repo)

        assert result.language is None

    def test_empty_topics_list(self):
        """Test repository with empty topics list."""
        github_repo = {
            "id": 222,
            "name": "no-topics-repo",
            "full_name": "user/no-topics-repo",
            "topics": [],
        }

        result = from_github_api(github_repo)

        assert result.topics == []

    def test_zero_counts(self):
        """Test repository with zero stars, forks, watchers, issues."""
        github_repo = {
            "id": 333,
            "name": "new-repo",
            "full_name": "user/new-repo",
            "stargazers_count": 0,
            "forks_count": 0,
            "watchers_count": 0,
            "open_issues_count": 0,
        }

        result = from_github_api(github_repo)

        assert result.stars == 0
        assert result.forks == 0
        assert result.watchers == 0
        assert result.open_issues == 0

    def test_large_numbers(self):
        """Test repository with large star/fork counts."""
        github_repo = {
            "id": 444,
            "name": "popular-repo",
            "full_name": "facebook/react",
            "stargazers_count": 250000,
            "forks_count": 50000,
            "watchers_count": 250000,
        }

        result = from_github_api(github_repo)

        assert result.stars == 250000
        assert result.forks == 50000
        assert result.watchers == 250000

    def test_various_language_names(self):
        """Test different programming language names."""
        languages = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#"]

        for lang in languages:
            github_repo = {
                "id": 555,
                "name": "test",
                "full_name": "user/test",
                "language": lang,
            }
            result = from_github_api(github_repo)
            assert result.language == lang

    def test_topics_order_preserved(self):
        """Test topics list order is preserved."""
        github_repo = {
            "id": 666,
            "name": "test",
            "full_name": "user/test",
            "topics": ["first", "second", "third"],
        }

        result = from_github_api(github_repo)

        assert result.topics == ["first", "second", "third"]

    def test_many_topics(self):
        """Test repository with many topics."""
        topics = [f"topic-{i}" for i in range(20)]
        github_repo = {
            "id": 777,
            "name": "test",
            "full_name": "user/test",
            "topics": topics,
        }

        result = from_github_api(github_repo)

        assert len(result.topics) == 20
        assert result.topics == topics

    def test_date_format_preserved(self):
        """Test date formats are preserved exactly as from GitHub."""
        github_repo = {
            "id": 888,
            "name": "test",
            "full_name": "user/test",
            "created_at": "2020-05-15T08:30:45Z",
            "updated_at": "2024-01-20T15:45:30Z",
        }

        result = from_github_api(github_repo)

        assert result.created_at == "2020-05-15T08:30:45Z"
        assert result.updated_at == "2024-01-20T15:45:30Z"

    def test_special_characters_in_name(self):
        """Test repository names with special characters."""
        github_repo = {
            "id": 999,
            "name": "my-awesome.project_123",
            "full_name": "user/my-awesome.project_123",
        }

        result = from_github_api(github_repo)

        assert result.name == "my-awesome.project_123"
        assert result.full_name == "user/my-awesome.project_123"

    def test_unicode_in_name(self):
        """Test repository names with Unicode characters."""
        github_repo = {
            "id": 1010,
            "name": "プロジェクト",
            "full_name": "user/プロジェクト",
        }

        result = from_github_api(github_repo)

        assert result.name == "プロジェクト"
        assert result.full_name == "user/プロジェクト"

    def test_url_variations(self):
        """Test different URL formats."""
        github_repo = {
            "id": 1111,
            "name": "test",
            "full_name": "organization/test",
            "html_url": "https://github.com/organization/test",
        }

        result = from_github_api(github_repo)

        assert result.url == "https://github.com/organization/test"

    def test_default_score_is_zero(self):
        """Test that default score in Repository model is 0.0."""
        github_repo = {
            "id": 1212,
            "name": "test",
            "full_name": "user/test",
        }

        result = from_github_api(github_repo)

        # Repository model should initialize score to 0.0
        assert result.score == 0.0

    def test_transformation_doesnt_modify_original(self):
        """Test transformation doesn't mutate the original dict."""
        github_repo = {
            "id": 1313,
            "name": "test",
            "full_name": "user/test",
            "stargazers_count": 100,
        }

        original_copy = github_repo.copy()
        from_github_api(github_repo)

        # Original should be unchanged
        assert github_repo == original_copy

    def test_missing_id_field(self):
        """Test transformation when id field is missing."""
        github_repo = {
            "name": "test",
            "full_name": "user/test",
        }

        result = from_github_api(github_repo)

        # get() returns None when key is missing
        assert result.id is None

    def test_empty_dict_handled(self):
        """Test transformation with empty dictionary."""
        github_repo = {}

        result = from_github_api(github_repo)

        assert isinstance(result, Repository)
        assert result.id is None
        assert result.name == ""
        assert result.full_name == ""
        assert result.url == ""

    def test_real_github_api_structure(self):
        """Test with realistic GitHub API response structure."""
        github_repo = {
            "id": 78136116,
            "node_id": "MDEwOlJlcG9zaXRvcnk3ODEzNjExNg==",
            "name": "vscode",
            "full_name": "microsoft/vscode",
            "private": False,
            "owner": {"login": "microsoft", "id": 6154722},
            "html_url": "https://github.com/microsoft/vscode",
            "description": "Visual Studio Code",
            "fork": False,
            "stargazers_count": 150000,
            "watchers_count": 150000,
            "forks_count": 25000,
            "open_issues_count": 5000,
            "language": "TypeScript",
            "topics": ["editor", "typescript", "vscode"],
            "created_at": "2017-01-01T00:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
        }

        result = from_github_api(github_repo)

        assert result.id == 78136116
        assert result.name == "vscode"
        assert result.full_name == "microsoft/vscode"
        assert result.url == "https://github.com/microsoft/vscode"
        assert result.stars == 150000
        assert result.watchers == 150000
        assert result.forks == 25000
        assert result.open_issues == 5000
        assert result.language == "TypeScript"
        assert "editor" in result.topics
