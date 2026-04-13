"""
Repository HTTP Routes

Handles HTTP requests for repository search endpoints.
Responsibilities:
- Parse and validate HTTP request parameters
- Instantiate and delegate to service layer
- Transform domain objects to HTTP responses
- Handle errors and format HTTP responses
- Logging HTTP-level concerns
"""

import logging

from flask import Blueprint, request, jsonify

from src.shared.models import SearchFilters
from src.shared import Config
from src.features.repositories.constants import POPULAR_LANGUAGES
from src.shared.core.exceptions import ExternalServiceException
from .validators import Validator, ValidationError
from .controller import repository_controller

repo_bp = Blueprint("repositories", __name__)
logger = logging.getLogger(__name__)


@repo_bp.route("/languages", methods=["GET"])
def get_language_suggestions():
    """
    Get programming language suggestions for autocomplete.

    Query parameters:
        q: Search query to filter languages (optional)

    Returns:
        JSON list of matching language names
    """
    try:
        query = request.args.get("q", "").strip().lower()

        if not query:
            # Return all popular languages if no query
            return jsonify(sorted(POPULAR_LANGUAGES)), 200

        # Filter languages that contain the query
        matching = [lang for lang in POPULAR_LANGUAGES if query in lang.lower()]

        return jsonify(sorted(matching)), 200

    except Exception as e:
        logger.exception(f"Unexpected error in get_language_suggestions: {e}")
        return jsonify({"error": "Internal server error"}), 500


@repo_bp.route("/repositories", methods=["POST"])
def get_repositories():
    """
    Search and rank repositories based on user filters.

    POST JSON body:
        languages: List of programming languages (or comma-separated string)
        created_after: ISO date (YYYY-MM-DD) for minimum creation date
        page: Page number (default: 1)
        per_page: Results per page (fixed at 25)

    Returns:
        JSON object with repository list and pagination metadata
    """
    try:
        data = request.get_json() or {}

        # Validate and create filters object
        filters = SearchFilters(
            languages=Validator.languages(data.get("languages")),
            created_after=Validator.iso_date(data.get("created_after"), "created_after"),
            page=Validator.int(data.get("page"), "page", default=1),
            per_page=Config.DEFAULT_PAGE_SIZE,
        )

        scored_repos, pagination_metadata = repository_controller.get_repositories(filters)
        return (
            jsonify(
                {
                    "items": scored_repos,
                    "pagination": pagination_metadata,
                }
            ),
            200,
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

    except ExternalServiceException as e:
        logger.error(f"External service error: {e.message} (status: {e.status_code})")
        return (
            jsonify(
                {
                    "error": "Failed to fetch repositories from external service",
                    "details": e.message,
                }
            ),
            503,
        )

    except Exception as e:
        logger.exception(f"Unexpected error in get_repositories: {e}")
        return jsonify({"error": "Internal server error"}), 500
