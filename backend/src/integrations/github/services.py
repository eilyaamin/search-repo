"""GitHub API service functions.

Provides functions for searching repositories and building GitHub search queries.
"""

from dataclasses import asdict
from typing import Dict, Any, List, Optional, Union

from src.shared import api_get, Config
from .dto import from_github_api


def search_repositories(
    url: str,
    query: str,
    token: Optional[str] = None,
    page: int = 1,
    per_page: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Search GitHub repositories with the given query.

    This function makes a single request to GitHub's search API. In the
    chunked caching architecture, this is called once per chunk.

    Args:
        url: GitHub API search endpoint URL
        query: GitHub search query string
        token: GitHub personal access token for authentication
        page: Page number for pagination (1-indexed)
        per_page: Number of results per page (defaults to GITHUB_CHUNK_SIZE)

    Returns:
        List of normalized repository dictionaries

    Raises:
        ExternalServiceException: If the API request fails
    """
    if per_page is None:
        per_page = Config.GITHUB_CHUNK_SIZE

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Add GitHub token if available for higher rate limits
    # GitHub uses 'token' prefix for classic PATs, not 'Bearer'
    if token:
        headers["Authorization"] = f"token {token}"

    params = {
        "q": query,
        # Sorting based on stars as it will get us closer to the best results
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": per_page,
    }

    data = api_get(url, headers=headers, params=params)

    # Extract items from GitHub API response and normalize each repository
    items = data.get("items", [])
    normalized_repos = [asdict(from_github_api(repo)) for repo in items]
    return normalized_repos


def build_github_query(
    languages: Optional[Union[str, List[str]]] = None,
    created_after: Optional[str] = None,
) -> str:
    """Build a GitHub search query string from filter parameters.

    Constructs a query compatible with GitHub's search API by combining
    language and date filters.

    GitHub Search Syntax:
    - Single language: "language:Python"
    - Multiple languages: "language:Python language:JavaScript"
      (GitHub automatically treats multiple language: filters as OR)
    - With date: "language:Python language:JavaScript created:>2020-01-01"

    Args:
        languages: Single language string or list of languages to filter by
        created_after: ISO date string (YYYY-MM-DD) for minimum creation date

    Returns:
        GitHub search query string
        Returns "stars:>0" as fallback if no filters provided
    """
    parts = []

    # language handling
    # GitHub's search API treats multiple language: filters as OR automatically
    # So "language:Python language:JavaScript" means Python OR JavaScript
    if languages:
        if isinstance(languages, str):
            parts.append(f"language:{languages}")
        else:
            # Add each language as a separate filter - GitHub treats these as OR
            for lang in languages:
                parts.append(f"language:{lang}")

    # created filter
    if created_after:
        parts.append(f"created:>{created_after}")

    # fallback to a valid query when no filters are provided
    return " ".join(parts).strip() if parts else "stars:>0"
