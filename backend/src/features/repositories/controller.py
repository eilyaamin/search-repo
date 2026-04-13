"""
Repository Controller

Coordinates the repository search workflow between the HTTP layer and service layer.
Responsibilities:
- Orchestrate application logic flow
- Instantiate and configure services
- Transform between layers
- Handle coordination between multiple services if needed

Architecture Initialization:
The controller wires together the three-layer architecture:
1. GitHubClient: Simple API client (just makes HTTP calls)
2. RepositoryDataService: Data orchestration (fetching, caching, prefetching)
3. RepositoryService: Business logic (scoring, sorting, UI pagination)
"""

import logging
from typing import Optional

from src.features.repositories.models import RepositorySearchResult
from src.shared.models import SearchFilters
from src.shared import Config
from src.features.repositories.domain.repo_scoring import calculate_repository_score
from src.shared.infrastructure.cache import RepositoryCache
from src.shared.infrastructure.data_service import RepositoryDataService
from src.integrations.github import GitHubClient
from .service import RepositoryService

logger = logging.getLogger(__name__)


class RepositoryController:
    """
    Controller for repository-related operations.

    Acts as a facade between the HTTP routes and the service layer,
    handling dependency injection and workflow orchestration.

    The controller initializes the full architecture stack:
    Cache → GitHubClient → RepositoryDataService → RepositoryService → Controller
    """

    def __init__(self):
        """Initialize the controller with its dependencies."""
        # Lazy initialization - created on first request
        self._service: Optional[RepositoryService] = None

    def _get_service(self) -> RepositoryService:
        """
        Lazy initialization of the service with its dependencies.

        This factory method creates the full service stack only when needed
        and caches it for subsequent requests. The architecture follows a
        clean separation of concerns:

        1. Cache: In-memory storage for fetched data
        2. GitHubClient: Simple API client (HTTP calls only)
        3. RepositoryDataService: Data orchestration layer
           - Handles progressive fetching (100-item chunks)
           - Manages caching and prefetching
           - Provider-agnostic
        4. RepositoryService: Business logic layer
           - Scoring and ranking
           - UI pagination (25-item pages)

        Returns:
            Configured RepositoryService instance
        """
        if self._service is None:
            # Build the service stack from bottom to top
            cache = RepositoryCache()
            provider = GitHubClient(token=Config.GITHUB_TOKEN)
            data_service = RepositoryDataService(
                provider=provider,
                cache=cache,
                page_size=Config.GITHUB_CHUNK_SIZE,
            )
            self._service = RepositoryService(
                data_service=data_service, scoring_fn=calculate_repository_score
            )

        return self._service

    def get_repositories(
        self, filters: SearchFilters
    ) -> RepositorySearchResult:
        """
        Search and rank repositories based on criteria.

        This is the main entry point for repository search operations.
        It coordinates the service layer to fetch, score, and rank repositories.

        The workflow:
        1. Controller receives filters from HTTP layer
        2. RepositoryService handles scoring and UI pagination
        3. RepositoryDataService handles data fetching and caching
        4. GitHubClient makes API calls as needed

        Args:
            filters: SearchFilters object containing validated search parameters

        Returns:
            Tuple of (list of repository DTOs, pagination metadata dict)

        Raises:
            ExternalServiceException: If the external API fails
        """
        # Get the service instance (lazy initialization on first call)
        service = self._get_service()

        # Delegate to service layer - now returns pagination metadata
        scored_repos, pagination_metadata = service.fetch_and_rank_repositories(filters)

        return scored_repos, pagination_metadata


# Singleton instance for the application
repository_controller = RepositoryController()
