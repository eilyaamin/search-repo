"""GitHub integration module.

Provides GitHub API client and utilities for searching repositories.
"""

from .services import build_github_query, search_repositories
from .client import GitHubClient
from .dto import from_github_api

__all__ = ["build_github_query", "search_repositories", "GitHubClient", "from_github_api"]