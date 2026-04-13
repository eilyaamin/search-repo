"""
Shared module exports.

This module provides centralized access to commonly used shared utilities,
configuration, and exceptions across the application.
"""

from .core.config import Config
from .core.exceptions import ExternalServiceException
from .infrastructure.http_client import api_get

__all__ = ["Config", "ExternalServiceException", "api_get"]