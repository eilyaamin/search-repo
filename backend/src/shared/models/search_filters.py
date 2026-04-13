"""Search filters model.

Defines search and pagination filters for repository queries.
"""

from dataclasses import dataclass
from typing import List, Optional

from src.shared import Config


@dataclass
class SearchFilters:
    """
    Search and pagination filters for repository queries.
    
    Attributes:
        languages: List of programming languages to filter by
        created_after: ISO date string (YYYY-MM-DD) for minimum creation date
        page: Page number for pagination (1-indexed)
        per_page: Number of results per page
    """
    languages: Optional[List[str]] = None
    created_after: Optional[str] = None
    page: int = 1
    per_page: int = Config.DEFAULT_PAGE_SIZE
