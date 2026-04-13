"""Domain layer for shared business logic and protocols.

This module contains domain models, protocols, and business logic that is
shared across different features of the application.
"""

from .repo_scoring import calculate_repository_score

__all__ = ["calculate_repository_score"]
