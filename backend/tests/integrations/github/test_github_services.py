"""
Unit tests for GitHub integration services.

Tests the build_github_query function which constructs GitHub-specific
search query strings from filter parameters.
"""

import pytest
from src.integrations.github.services import build_github_query


class TestBuildGitHubQuery:
    """Test suite for GitHub query building."""

    def test_single_language_query(self):
        """Test building query with single language."""
        query = build_github_query(languages="Python")
        assert query == "language:Python"

    def test_multiple_languages_as_list(self):
        """Test building query with multiple languages as list."""
        query = build_github_query(languages=["Python", "JavaScript", "Go"])
        assert "language:Python" in query
        assert "language:JavaScript" in query
        assert "language:Go" in query

    def test_multiple_languages_or_logic(self):
        """Test multiple languages are separated correctly for OR logic."""
        query = build_github_query(languages=["Python", "JavaScript"])
        # Should be space-separated for GitHub's OR logic
        assert query == "language:Python language:JavaScript"

    def test_created_after_filter(self):
        """Test building query with created_after date."""
        query = build_github_query(created_after="2020-01-01")
        assert query == "created:>2020-01-01"

    def test_language_and_date_combined(self):
        """Test building query with both language and date filters."""
        query = build_github_query(languages="Python", created_after="2020-01-01")
        assert "language:Python" in query
        assert "created:>2020-01-01" in query

    def test_multiple_languages_and_date(self):
        """Test building query with multiple languages and date."""
        query = build_github_query(
            languages=["Python", "JavaScript"], created_after="2020-01-01"
        )
        assert "language:Python" in query
        assert "language:JavaScript" in query
        assert "created:>2020-01-01" in query

    def test_no_filters_returns_fallback(self):
        """Test query with no filters returns default fallback."""
        query = build_github_query()
        assert query == "stars:>0"

    def test_none_languages_returns_fallback(self):
        """Test None languages returns fallback."""
        query = build_github_query(languages=None, created_after=None)
        assert query == "stars:>0"

    def test_empty_list_languages_returns_fallback(self):
        """Test empty list of languages returns fallback."""
        query = build_github_query(languages=[], created_after=None)
        assert query == "stars:>0"

    def test_empty_string_language_returns_fallback(self):
        """Test empty string language is ignored."""
        query = build_github_query(languages="", created_after=None)
        assert query == "stars:>0"

    def test_none_created_after_ignored(self):
        """Test None created_after is ignored."""
        query = build_github_query(languages="Python", created_after=None)
        assert query == "language:Python"
        assert "created:" not in query

    def test_empty_string_created_after_ignored(self):
        """Test empty string created_after is ignored."""
        query = build_github_query(languages="Python", created_after="")
        assert query == "language:Python"
        assert "created:" not in query

    def test_preserves_language_case(self):
        """Test language names preserve their case."""
        query = build_github_query(languages=["TypeScript", "javascript"])
        assert "language:TypeScript" in query
        assert "language:javascript" in query

    def test_special_characters_in_language(self):
        """Test languages with special characters (if valid)."""
        query = build_github_query(languages="C++")
        assert "language:C++" in query

    def test_single_language_in_list(self):
        """Test single language provided as list."""
        query = build_github_query(languages=["Python"])
        assert query == "language:Python"

    def test_date_format_preserved(self):
        """Test date format is preserved exactly."""
        query = build_github_query(created_after="2024-12-31")
        assert "created:>2024-12-31" in query

    def test_multiple_languages_order_preserved(self):
        """Test order of languages is preserved."""
        query = build_github_query(languages=["Rust", "Go", "Python"])
        # Check they appear in order
        rust_idx = query.index("Rust")
        go_idx = query.index("Go")
        python_idx = query.index("Python")
        assert rust_idx < go_idx < python_idx

    def test_whitespace_handling(self):
        """Test query has single spaces between parts."""
        query = build_github_query(
            languages=["Python", "JavaScript"], created_after="2020-01-01"
        )
        # Should not have multiple consecutive spaces
        assert "  " not in query

    def test_no_leading_or_trailing_whitespace(self):
        """Test query has no leading or trailing whitespace."""
        query = build_github_query(languages="Python", created_after="2020-01-01")
        assert query == query.strip()

    def test_single_language_string_not_list(self):
        """Test single language as string produces correct format."""
        query_string = build_github_query(languages="Python")
        query_list = build_github_query(languages=["Python"])
        assert query_string == query_list

    def test_complex_real_world_query(self):
        """Test complex realistic query."""
        query = build_github_query(
            languages=["Python", "JavaScript", "TypeScript", "Go"],
            created_after="2023-01-01",
        )
        assert "language:Python" in query
        assert "language:JavaScript" in query
        assert "language:TypeScript" in query
        assert "language:Go" in query
        assert "created:>2023-01-01" in query

    def test_unicode_language_names(self):
        """Test Unicode characters in language names work."""
        # Some languages might have Unicode (though rare)
        query = build_github_query(languages=["日本語"])
        assert "language:日本語" in query

    def test_date_only_query(self):
        """Test query with only date filter, no languages."""
        query = build_github_query(languages=None, created_after="2023-06-15")
        assert query == "created:>2023-06-15"

    def test_dash_separated_language_names(self):
        """Test language names with dashes."""
        query = build_github_query(languages="Objective-C")
        assert "language:Objective-C" in query
