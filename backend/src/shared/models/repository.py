"""Repository domain model.

Represents a source code repository with its metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Repository:
    """
    Domain model for a source code repository.
    
    Attributes:
        id: Unique identifier from the provider (e.g., GitHub)
        name: Repository name
        full_name: Full repository name including owner (e.g., "owner/repo")
        url: URL to the repository web page
        stars: Number of stars/favorites
        forks: Number of forks
        watchers: Number of watchers
        open_issues: Number of open issues
        language: Primary programming language (None if not detected)
        topics: List of repository topics/tags
        created_at: ISO timestamp of repository creation
        updated_at: ISO timestamp of last update
        score: Calculated quality score (set by scoring algorithm)
    """
    id: int
    name: str
    full_name: str
    url: str
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    language: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: float = 0.0
