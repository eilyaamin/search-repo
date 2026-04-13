"""Pagination metadata model.

Defines pagination metadata for API responses.
"""

"""Repository domain model.

Represents a source code repository with its metadata.
"""

from dataclasses import dataclass
from typing import List

from src.shared.models import PaginationMetadata, Repository


@dataclass
class RepositorySearchResult:
    """
    Model for a source code repository.
    """
    items: List[Repository]
    pagination: PaginationMetadata
