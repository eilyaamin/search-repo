"""HTTP client utilities.

Provides wrapper functions for making HTTP requests with consistent
error handling and exception translation.
"""

from typing import Dict, Any, Optional

import requests

from src.shared.core.exceptions import ExternalServiceException


def api_get(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """Make a GET request to an external API with error handling.
    
    Wraps requests.get to provide consistent exception handling and
    automatic JSON response parsing.
    
    Args:
        url: The URL to request
        headers: Optional HTTP headers dictionary
        params: Optional query parameters dictionary
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        Parsed JSON response as a Python dictionary
        
    Raises:
        ExternalServiceException: If the request fails or returns an error status
    """
    try:
        response = requests.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise ExternalServiceException(
            status_code=0,
            message=str(e),
        )

    if not response.ok:
        raise ExternalServiceException(
            status_code=response.status_code,
            message=response.text,
        )

    return response.json()
