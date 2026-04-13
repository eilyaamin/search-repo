"""Pagination metadata model.

Defines pagination metadata for API responses.
"""

from dataclasses import dataclass
from typing import TypedDict

@dataclass
class PaginationMetadata(TypedDict):
    """
    Pagination metadata for API responses.
    
    Attributes:
        current_page: Current page number (1-indexed)
        per_page: Number of items per page
        has_next: Whether there is a next page
        has_previous: Whether there is a previous page
    """
    current_page: int
    per_page: int
    has_next: bool
    has_previous: bool
