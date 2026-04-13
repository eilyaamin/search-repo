import logging
import threading
from typing import List, Dict, Any

from src.shared.models import SearchFilters, Repository
from src.shared.infrastructure.cache import RepositoryCache
from src.shared import Config
from src.integrations.repository_provider import RepositoryProvider

logger = logging.getLogger(__name__)


class RepositoryDataService:
    """
    Orchestrates repository data retrieval, caching, and background loading.

    Responsibilities:
    - Ensure sufficient data is available for a request
    - Manage cache lifecycle
    - Prevent duplicate concurrent fetches
    - Proactively load additional data when needed
    """

    MAX_RESULTS = 1000

    def __init__(
        self,
        provider: RepositoryProvider,
        cache: RepositoryCache,
        page_size: int = Config.GITHUB_CHUNK_SIZE,
    ):
        self.provider = provider
        self.cache = cache
        self.page_size = page_size

        self._inflight = set()
        self._lock = threading.Lock()

    # =========================
    # Public API
    # =========================

    def get_repositories(self, filters: SearchFilters) -> List[Repository]:
        query = self.provider.build_query(filters)
        required_items = filters.page * filters.per_page

        self._ensure_data_availability(query, required_items)

        cache_entry = self.cache.get(query)
        if not cache_entry:
            logger.warning(f"Cache miss after load for query={query}")
            return []

        repositories = [Repository(**r) for r in cache_entry["repos"]]

        self._schedule_prefetch_if_needed(query, required_items, cache_entry)

        return repositories

    # =========================
    # Data loading
    # =========================

    def _ensure_data_availability(self, query: str, required_items: int) -> None:
        cache_entry = self.cache.get(query)

        if not cache_entry:
            self._fetch_page(query, 1, initial=True)
            cache_entry = self.cache.get(query)

        while self._requires_additional_data(cache_entry, required_items):
            next_page = cache_entry["pages_loaded"] + 1
            self._fetch_page(query, next_page)
            cache_entry = self.cache.get(query)

    def _requires_additional_data(self, cache_entry: Dict[str, Any], required_items: int) -> bool:
        current_count = len(cache_entry["repos"])

        return (
            current_count < required_items
            and not cache_entry["last_page"]
            and current_count < self.MAX_RESULTS
        )

    # =========================
    # Fetching
    # =========================

    def _fetch_page(self, query: str, page: int, initial: bool = False) -> None:
        key = f"{query}:{page}"

        if not self._try_acquire_fetch_slot(key):
            logger.debug(f"Skipping duplicate fetch: {key}")
            return

        try:
            if self._is_page_cached(query, page):
                return

            logger.debug(f"Fetching page {page} for query={query}")
            repositories = self.provider.fetch_repositories(query, page)

            is_last_page = len(repositories) < self.page_size

            if initial:
                self.cache.set(
                    query=query,
                    repos=repositories,
                    pages_loaded=1,
                    last_page=is_last_page,
                )
            else:
                self.cache.add_page(
                    query=query,
                    page_repos=repositories,
                    page_number=page,
                    is_last_page=is_last_page,
                )

        finally:
            self._release_fetch_slot(key)

    def _is_page_cached(self, query: str, page: int) -> bool:
        entry = self.cache.get(query)
        return entry and entry["pages_loaded"] >= page

    # =========================
    # Prefetching
    # =========================

    def _schedule_prefetch_if_needed(
        self,
        query: str,
        required_items: int,
        cache_entry: Dict[str, Any],
    ) -> None:
        loaded_items = len(cache_entry["repos"])

        if not self._should_schedule_prefetch(required_items, loaded_items, cache_entry):
            return

        next_page = cache_entry["pages_loaded"] + 1

        logger.debug(f"Scheduling prefetch for page {next_page} query={query}")

        thread = threading.Thread(
            target=lambda: self._fetch_page(query, next_page),
            daemon=True,
        )
        thread.start()

    def _should_schedule_prefetch(
        self,
        required_items: int,
        loaded_items: int,
        cache_entry: Dict[str, Any],
    ) -> bool:
        if cache_entry["last_page"]:
            return False

        if loaded_items >= self.MAX_RESULTS:
            return False

        if loaded_items == 0:
            return False

        return (required_items / loaded_items) >= 0.75

    # =========================
    # Concurrency control
    # =========================

    def _try_acquire_fetch_slot(self, key: str) -> bool:
        with self._lock:
            if key in self._inflight:
                return False
            self._inflight.add(key)
            return True

    def _release_fetch_slot(self, key: str) -> None:
        with self._lock:
            self._inflight.discard(key)
