"""
Repository Cache

In-memory cache for repository search results. Cache is organized
by query string to avoid redundant API calls. Each cache entry tracks
pagination metadata to support progressive fetching and prefetching.
"""

from typing import Dict, Any, List, Optional


class RepositoryCache:
    """
    In-memory cache for repository search results.

    Caches repositories by query string and tracks metadata for each query:
    - repos: List of all fetched repositories
    - pages_loaded: Number of pages that have been fetched
    - last_page: Whether we've reached the last page of results

    This metadata enables:
    - Avoiding redundant API calls for the same query
    - Progressive loading as pagination progresses
    - Smart prefetching decisions based on consumption
    - Rate limit protection by minimizing API requests

    Cache persists for the lifetime of the application instance and is
    lost on application restart.
    
    Cache Entry Structure:
    {
        "query_string": {
            "repos": List[Dict[str, Any]],
            "pages_loaded": int,
            "last_page": bool
        }
    }
    """

    def __init__(self):
        """Initialize an empty cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached entry for a query.

        Args:
            query: The search query string used as cache key

        Returns:
            Cache entry dict with 'repos', 'pages_loaded', and 'last_page',
            or None if not cached
        """
        return self._cache.get(query)

    def has(self, query: str) -> bool:
        """
        Check if a query exists in the cache.

        Args:
            query: The search query string

        Returns:
            True if query is cached, False otherwise
        """
        return query in self._cache

    def set(
        self,
        query: str,
        repos: List[Dict[str, Any]],
        pages_loaded: int,
        last_page: bool,
    ):
        """
        Store or update cache entry for a query.

        Args:
            query: The search query string used as cache key
            repos: List of repository dictionaries
            pages_loaded: Number of pages that have been fetched
            last_page: Whether this is the last page (no more results available)
        """
        self._cache[query] = {
            "repos": repos,
            "pages_loaded": pages_loaded,
            "last_page": last_page,
        }

    def add_page(
        self,
        query: str,
        page_repos: List[Dict[str, Any]],
        page_number: int,
        is_last_page: bool,
    ):
        """
        Add a newly fetched page to an existing cache entry.

        Updates the cache by appending new repositories and updating metadata.
        If the cache entry doesn't exist, it creates one.
        
        Includes defensive deduplication to prevent duplicate repositories
        from being added if the same page is somehow fetched twice.

        Args:
            query: The search query string
            page_repos: List of repositories from the new page
            page_number: The page number being added (for metadata tracking)
            is_last_page: Whether this is the last page of results
        """
        if not self.has(query):
            # Initialize cache entry if it doesn't exist
            self.set(query, page_repos, pages_loaded=1, last_page=is_last_page)
        else:
            # Append to existing cache entry with deduplication
            entry = self._cache[query]
            
            # Build set of existing IDs for fast lookup
            existing_ids = {repo["id"] for repo in entry["repos"]}
            
            # Only add repos that aren't already in cache
            new_repos = [repo for repo in page_repos if repo["id"] not in existing_ids]
            
            if new_repos:
                entry["repos"].extend(new_repos)
            
            entry["pages_loaded"] = page_number
            entry["last_page"] = is_last_page

    def invalidate(self, query: str):
        """
        Remove a specific query from the cache.

        Args:
            query: The search query string to invalidate
        """
        if query in self._cache:
            del self._cache[query]

    def clear(self):
        """Clear all cached data."""
        self._cache.clear()
