"""
GitHub Repository Provider

Simple GitHub API client that implements the RepositoryProvider protocol.
This client is responsible ONLY for making API calls to GitHub - all caching,
prefetching, and orchestration logic is handled by RepositoryDataService.

Separation of Concerns:
- GitHubClient: Makes API calls, handles GitHub-specific query building
- RepositoryDataService: Orchestrates fetching, caching, and prefetching
- RepositoryService: Handles business logic (scoring, sorting, UI pagination)
"""

import logging
from typing import List, Dict, Any, Optional

from src.integrations.repository_provider import RepositoryProvider
from src.shared import Config
from src.shared.models import SearchFilters
from . import search_repositories
from .services import build_github_query

logger = logging.getLogger(__name__)


class GitHubClient(RepositoryProvider):
    """
    GitHub API client implementing RepositoryProvider protocol.
    
    This is a minimal, focused client that only handles:
    1. Building GitHub-specific search queries
    2. Making paginated API calls to GitHub
    3. Returning normalized repository data
    
    All caching, prefetching, and data orchestration is delegated to
    RepositoryDataService, making this client simple, testable, and reusable.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token for authentication (optional)
                  Using a token provides higher rate limits (5000 req/hr vs 60 req/hr)
        """
        self.token = token
        self.github_url = f"{Config.GITHUB_API_URL}/search/repositories"

    def fetch_repositories(self, query: str, page: int) -> List[Dict[str, Any]]:
        """
        Fetch a single page of repositories from GitHub API.
        
        This method makes one API call and returns the results. It does not
        handle caching or prefetching - those concerns are handled by
        RepositoryDataService.
        
        Args:
            query: GitHub search query string (e.g., "language:Python created:>2020-01-01")
            page: Page number to fetch (1-indexed)
            
        Returns:
            List of normalized repository dictionaries (up to 100 items).
            Returns empty list if no results or if we've hit API limits.
            
        Raises:
            ExternalServiceException: If the API request fails (except for known limits)
        """
        try:
            repos = search_repositories(
                url=self.github_url,
                query=query,
                token=self.token,
                page=page,
                per_page=Config.GITHUB_CHUNK_SIZE,
            )
            
            return repos
            
        except Exception as e:
            # Check for known GitHub API limits
            if hasattr(e, 'status_code'):
                if e.status_code == 422:
                    # GitHub's 1000 result limit - return empty list to signal no more results
                    return []
                
                if e.status_code == 403:
                    # Rate limit exceeded
                    logger.error("GitHub rate limit exceeded")
                    raise
            
            # Re-raise other exceptions
            logger.error(f"Failed to fetch GitHub repositories: {e}")
            raise
    
    def build_query(self, filters: SearchFilters) -> str:
        """
        Build a GitHub-specific query string from filters.
        
        Args:
            filters: SearchFilters object with languages and date filters
            
        Returns:
            GitHub search query string
        """
        return build_github_query(
            languages=filters.languages,
            created_after=filters.created_after,
        )
