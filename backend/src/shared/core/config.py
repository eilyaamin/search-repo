"""Application configuration.

Centralized configuration values for the application.
"""

import os


class Config:
    """Configuration constants for external services and application behavior."""
    
    GITHUB_API_URL = "https://api.github.com"
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)  # GitHub personal access token for higher rate limits
    GITHUB_MAX_PER_PAGE = 100  # GitHub's hard limit per API request
    GITHUB_CHUNK_SIZE = 100  # Fetch 100 items per chunk (1 API call)
    DEFAULT_PAGE_SIZE = 25  # Fixed page size for frontend pagination