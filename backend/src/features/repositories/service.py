"""
Repository Application Service

Orchestrates the repository search workflow, applying business logic
such as scoring, sorting, and pagination. This service is provider-agnostic
and focuses on domain logic, delegating data fetching to RepositoryDataService.

Architectural Layers:
- RepositoryService (this): Business logic (scoring, sorting, UI pagination)
- RepositoryDataService: Data orchestration (fetching, caching, prefetching)
- GitHubClient: API calls only
"""

from dataclasses import asdict
from typing import Callable

from src.features.repositories.models import RepositorySearchResult
from src.shared.infrastructure.data_service import RepositoryDataService
from src.shared.utils.pagination import paginate
from src.shared.models import PaginationMetadata, SearchFilters, Repository


class RepositoryService:
    """
    Application service for repository search and ranking.

    This service orchestrates the complete workflow:
    1. Fetch ALL loaded repositories from data service
    2. Calculate quality scores for all repositories
    3. Sort by score (best first)
    4. Paginate results for UI (UI-level pagination)
    5. Return scored repositories

    The data service (RepositoryDataService) handles data-level concerns
    (chunked fetching, caching, prefetching), while this service focuses
    purely on business logic (scoring and ranking).

    Clear Separation:
    - Data-level pagination: Handled by RepositoryDataService (100-item chunks)
    - UI-level pagination: Handled here (25-item pages for frontend)
    """

    def __init__(
        self,
        data_service: RepositoryDataService,
        scoring_fn: Callable[[Repository], float],
    ):
        """
        Initialize the repository service.

        Args:
            data_service: RepositoryDataService for data orchestration
            scoring_fn: Function to calculate repository scores (accepts Repository model)
        """
        self.data_service = data_service
        self.scoring_fn = scoring_fn

    def fetch_and_rank_repositories(
        self, filters: SearchFilters
    ) -> RepositorySearchResult:
        """
        Fetch, score, sort, and paginate repositories.

        This method implements the core business logic:
        - Fetches ALL currently loaded repositories from data service
          (data service handles ensuring enough data is loaded)
        - Applies scoring algorithm to all repositories
        - Sorts by score (best first)
        - Paginates the sorted results for UI
        - Returns the requested page with pagination metadata

        The data service intelligently fetches and caches data as needed,
        including progressive prefetching when users approach the edge of
        loaded data. This service remains focused on scoring and ranking.

        Args:
            filters: SearchFilters object containing validated search parameters

        Returns:
            Tuple of (list of repository DTOs for requested page, pagination metadata)

        Raises:
            ExternalServiceException: If the data service fails to fetch data
        """
        # Step 1: Get all currently loaded repositories from data service
        # Data service handles caching, fetching, and prefetching transparently
        # Returns Repository domain models (not dicts)
        all_repos = self.data_service.get_repositories(filters)

        # Step 2: Calculate scores for each repository
        for repo in all_repos:
            repo.score = self.scoring_fn(repo)

        # Step 3: Sort by score (descending - highest scores first)
        sorted_repos = sorted(all_repos, key=lambda r: r.score, reverse=True)

        # Step 4: Paginate the sorted results for UI
        # This is UI-level pagination (25 items per page), distinct from
        # data-level pagination (100-item chunks from API)
        paginated_repos = paginate(sorted_repos, filters.page, filters.per_page)

        # Step 5: Convert Repository objects to dicts for API response
        paginated_dicts = [asdict(repo) for repo in paginated_repos]

        # Step 6: Calculate pagination metadata
        metadata = PaginationMetadata(
            current_page=filters.page,
            per_page=filters.per_page,
            has_next=len(paginated_repos) == filters.per_page,
            has_previous=filters.page > 1,
        )

        # Return scored domain objects and pagination metadata
        return paginated_dicts, metadata
