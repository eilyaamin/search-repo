"""Custom exceptions for the application.

Defines domain-specific exceptions for better error handling and reporting.
"""


class ExternalServiceException(Exception):
    """Exception raised when an external service (e.g., GitHub API) fails.
    
    Attributes:
        status_code: HTTP status code from the failed request
        message: Error message describing the failure
    """
    
    def __init__(self, status_code, message):
        """Initialize the exception with status code and message.
        
        Args:
            status_code: HTTP status code from the failed request
            message: Error message describing the failure
        """
        self.status_code = status_code
        self.message = message
        super().__init__(f"External API Error {status_code}: {message}")