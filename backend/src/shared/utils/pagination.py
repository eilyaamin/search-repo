"""Pagination utilities.

Provides functions for paginating lists of items.
"""

from __future__ import annotations
from typing import List, Any


def paginate(items: List[Any], page: int, per_page: int) -> List[Any]:
    """Paginate a list of items.
    
    Extracts a specific page from a list of items based on page number
    and items per page.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed, min: 1)
        per_page: Number of items per page (min: 1)
        
    Returns:
        List containing items for the requested page
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]
