"""
Repository Provider Protocol

Defines the interface for repository data providers that work with the
RepositoryDataService. This protocol ensures provider-agnostic data orchestration.
"""

from typing import List, Dict, Any, Protocol

from src.shared.models import SearchFilters


class RepositoryProvider(Protocol):
    """
    Protocol for providers that fetch repositories in pages.
    
    This is the standard interface that all providers must implement to work
    with RepositoryDataService. The provider only needs to handle API
    calls - no caching or orchestration logic.
    """
    
    def fetch_repositories(self, query: str, page: int) -> List[Dict[str, Any]]:
        """
        Fetch a single page of repositories from the API.
        
        Args:
            query: Search query string (provider-specific format)
            page: Page number to fetch (1-indexed)
            
        Returns:
            List of repository dictionaries (empty list if no more results)
            
        Raises:
            ExternalServiceException: If the API request fails
        """
        ...
    
    def build_query(self, filters: SearchFilters) -> str:
        """
        Build a provider-specific query string from filters.
        
        Args:
            filters: SearchFilters object with languages and date filters
            
        Returns:
            Provider-specific query string
        """
        ...
