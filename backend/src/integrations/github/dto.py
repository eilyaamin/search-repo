"""Data Transfer Objects for GitHub API.

Provides functions to transform GitHub API responses into internal domain models.
"""

from typing import Dict, Any

from src.shared.models import Repository


def from_github_api(repo: Dict[str, Any]) -> Repository:
    """
    Normalize a GitHub API repository response to internal domain format.
    
    Args:
        repo: Raw repository dict from GitHub API
        
    Returns:
        Repository domain model instance
    """
    return Repository(
        id=repo.get("id"),
        name=repo.get("name", ""),
        full_name=repo.get("full_name", ""),
        url=repo.get("html_url", ""),
        stars=repo.get("stargazers_count", 0),
        forks=repo.get("forks_count", 0),
        watchers=repo.get("watchers_count", 0),
        open_issues=repo.get("open_issues_count", 0),
        language=repo.get("language"),
        topics=repo.get("topics", []),
        created_at=repo.get("created_at"),
        updated_at=repo.get("updated_at"),
    )
