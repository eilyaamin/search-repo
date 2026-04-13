"""Request validation utilities.

Provides validation functions for HTTP request parameters with
consistent error handling and type coercion.
"""

from datetime import datetime
from typing import Optional, List, Union


class ValidationError(Exception):
    """Exception raised when request validation fails."""
    pass


class Validator:
    """Static utility class for validating and normalizing request parameters."""
    
    @staticmethod
    def int(value, name, default=None, min_value=1, max_value=100):
        """Validate and normalize an integer parameter.
        
        Args:
            value: The value to validate (can be None, int, or string)
            name: Name of the parameter (for error messages)
            default: Default value if value is None
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            
        Returns:
            Validated integer value or default
            
        Raises:
            ValidationError: If value is not a valid integer or out of range
        """
        if value is None:
            return default

        try:
            value = int(value)
        except ValueError:
            raise ValidationError(f"{name} must be an integer")

        if min_value is not None and value < min_value:
            raise ValidationError(f"{name} must be >= {min_value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"{name} must be <= {max_value}")

        return value

    @staticmethod
    def iso_date(value, name):
        """Validate and normalize an ISO date parameter.
        
        Accepts full ISO datetime strings or date-only strings and normalizes
        them to YYYY-MM-DD format for GitHub API compatibility.
        
        Args:
            value: The date value to validate (ISO format string or None)
            name: Name of the parameter (for error messages)
            
        Returns:
            Normalized date string in YYYY-MM-DD format, or None if value is None
            
        Raises:
            ValidationError: If value is not a valid ISO date format
        """
        if value is None:
            return None
        try:
            # Normalize to an ISO date string (YYYY-MM-DD) which GitHub search understands.
            # Accepts either a date or full ISO datetime.
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            raise ValidationError(
                f"{name} must be ISO format (YYYY-MM-DD or full ISO datetime)"
            )

    @staticmethod
    def languages(value):
        """Validate and normalize a list of programming languages.
        
        Accepts either a list of strings or a comma-separated string and
        normalizes to a list of trimmed non-empty language names.
        
        Args:
            value: Languages as list or comma-separated string (or None)
            
        Returns:
            List of normalized language strings, or None if value is None
            
        Raises:
            ValidationError: If value is not a list/string or is empty
        """
        if value is None:
            return None

        # Accept both list and comma-separated string for backward compatibility
        if isinstance(value, list):
            languages = [str(v).strip() for v in value if str(v).strip()]
        elif isinstance(value, str):
            languages = [v.strip() for v in value.split(",") if v.strip()]
        else:
            raise ValidationError("languages must be a list or comma-separated string")

        if not languages:
            raise ValidationError("languages must contain at least one language")

        return languages