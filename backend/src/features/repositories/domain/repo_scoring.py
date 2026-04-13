import math
from datetime import datetime

from src.shared.models import Repository


def calculate_repository_score(repo: Repository) -> float:
    """
    Calculate a quality score for a repository based on popularity and recency.

    The score combines:
    - Popularity (80%): Stars (40%), Forks (16%), Watchers (8%)
    - Recency (20%): Based on 30-day half-life decay
    
    Args:
        repo: Repository domain model with metrics and metadata
        
    Returns:
        Quality score as a float (higher is better)
    """

    # Log scaling for popularity metrics
    stars_score = math.log(repo.stars + 1)
    forks_score = math.log(repo.forks + 1)
    watchers_score = math.log(repo.watchers + 1)

    popularity_score = stars_score * 0.5 + forks_score * 0.2 + watchers_score * 0.1

    # Recency (30-day half-life)
    recency_factor = 1.0
    if repo.updated_at:
        try:
            updated = datetime.strptime(repo.updated_at, "%Y-%m-%dT%H:%M:%SZ")
            days_since_update = (datetime.utcnow() - updated).days
            recency_factor = 0.5 ** (days_since_update / 30)
        except (ValueError, TypeError):
            recency_factor = 1.0

    final_score = popularity_score * 0.8 + recency_factor * 0.2

    return final_score
