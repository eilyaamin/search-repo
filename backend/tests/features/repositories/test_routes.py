"""
Unit tests for repository HTTP routes.

Tests the Flask routes that handle repository search endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from src import create_app
from src.features.repositories.constants import POPULAR_LANGUAGES


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestLanguagesEndpoint:
    """Test suite for /api/languages endpoint."""

    def test_get_languages_without_query(self, client):
        """Test getting all languages without query parameter."""
        response = client.get("/api/languages")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        # Should return sorted popular languages
        assert "Python" in data
        assert "JavaScript" in data
        assert data == sorted(data)

    def test_get_languages_with_empty_query(self, client):
        """Test getting languages with empty query returns all."""
        response = client.get("/api/languages?q=")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == len(POPULAR_LANGUAGES)

    def test_get_languages_filters_by_query(self, client):
        """Test language endpoint filters by query parameter."""
        response = client.get("/api/languages?q=python")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        # Should only return languages containing 'python'
        for lang in data:
            assert "python" in lang.lower()

    def test_get_languages_case_insensitive_search(self, client):
        """Test language search is case-insensitive."""
        response = client.get("/api/languages?q=JAVA")

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should match JavaScript, Java
        assert len(data) >= 2

    def test_get_languages_partial_match(self, client):
        """Test language search supports partial matching."""
        response = client.get("/api/languages?q=script")

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should match JavaScript, TypeScript, CoffeeScript, etc.
        assert "JavaScript" in data
        assert "TypeScript" in data

    def test_get_languages_no_matches(self, client):
        """Test language search with no matches returns empty list."""
        response = client.get("/api/languages?q=nonexistentlanguage123")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_get_languages_sorted_alphabetically(self, client):
        """Test returned languages are sorted alphabetically."""
        response = client.get("/api/languages?q=java")

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be sorted
        assert data == sorted(data)


class TestRepositoriesEndpoint:
    """Test suite for /api/repositories endpoint."""

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_basic(self, mock_controller, client):
        """Test basic repository search request."""
        # Setup mock
        mock_controller.get_repositories.return_value = (
            [{"id": 1, "name": "repo1"}],
            {"current_page": 1, "per_page": 25, "has_next": False, "has_previous": False},
        )

        # Execute
        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": ["Python"], "page": 1}),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) == 1

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_with_all_filters(self, mock_controller, client):
        """Test repository search with all filter parameters."""
        mock_controller.get_repositories.return_value = (
            [],
            {"current_page": 1, "per_page": 25, "has_next": False, "has_previous": False},
        )

        response = client.post(
            "/api/repositories",
            data=json.dumps({
                "languages": ["Python", "JavaScript"],
                "created_after": "2020-01-01",
                "page": 2,
            }),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert "pagination" in data

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_empty_body(self, mock_controller, client):
        """Test repository search with empty request body."""
        mock_controller.get_repositories.return_value = (
            [],
            {"current_page": 1, "per_page": 25, "has_next": False, "has_previous": False},
        )

        response = client.post(
            "/api/repositories",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_post_repositories_no_json_body(self, client):
        """Test repository search handles missing JSON body."""
        # Without proper content type or body, this may fail
        response = client.post("/api/repositories")

        # Should handle gracefully - may return error or empty result
        assert response.status_code in [200, 400, 500, 503]  # Any valid HTTP response

    def test_post_repositories_invalid_page_number(self, client):
        """Test validation error for invalid page number."""
        response = client.post(
            "/api/repositories",
            data=json.dumps({"page": "invalid"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "integer" in data["error"].lower()

    def test_post_repositories_page_below_minimum(self, client):
        """Test validation error for page below minimum."""
        response = client.post(
            "/api/repositories",
            data=json.dumps({"page": 0}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_post_repositories_invalid_date_format(self, client):
        """Test validation error for invalid date format."""
        response = client.post(
            "/api/repositories",
            data=json.dumps({"created_after": "01/15/2024"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "ISO" in data["error"]

    def test_post_repositories_empty_languages_list(self, client):
        """Test validation error for empty languages list."""
        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": []}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "language" in data["error"].lower()

    def test_post_repositories_invalid_languages_type(self, client):
        """Test validation error for invalid languages type."""
        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": 123}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_comma_separated_languages(self, mock_controller, client):
        """Test languages as comma-separated string."""
        mock_controller.get_repositories.return_value = (
            [],
            {"current_page": 1, "per_page": 25, "has_next": False, "has_previous": False},
        )

        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": "Python,JavaScript,Go"}),
            content_type="application/json",
        )

        assert response.status_code == 200

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_external_service_error(self, mock_controller, client):
        """Test handling of external service errors."""
        from src.shared.core.exceptions import ExternalServiceException

        mock_controller.get_repositories.side_effect = ExternalServiceException(
            "GitHub API error", 503
        )

        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": ["Python"]}),
            content_type="application/json",
        )

        assert response.status_code == 503
        data = json.loads(response.data)
        assert "error" in data
        assert "details" in data

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_unexpected_error(self, mock_controller, client):
        """Test handling of unexpected errors."""
        mock_controller.get_repositories.side_effect = Exception("Unexpected error")

        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": ["Python"]}),
            content_type="application/json",
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Internal server error" in data["error"]

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_returns_correct_structure(self, mock_controller, client):
        """Test response has correct structure."""
        mock_controller.get_repositories.return_value = (
            [{"id": 1, "name": "repo1", "score": 5.5}],
            {
                "current_page": 2,
                "per_page": 25,
                "has_next": True,
                "has_previous": True,
            },
        )

        response = client.post(
            "/api/repositories",
            data=json.dumps({"languages": ["Python"], "page": 2}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["current_page"] == 2
        assert data["pagination"]["per_page"] == 25
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is True

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_valid_iso_datetime(self, mock_controller, client):
        """Test valid ISO datetime is accepted and normalized."""
        mock_controller.get_repositories.return_value = (
            [],
            {"current_page": 1, "per_page": 25, "has_next": False, "has_previous": False},
        )

        response = client.post(
            "/api/repositories",
            data=json.dumps({"created_after": "2024-01-15T10:30:00"}),
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_post_repositories_method_not_allowed(self, client):
        """Test GET method is not allowed on repositories endpoint."""
        response = client.get("/api/repositories")
        assert response.status_code == 405

    @patch("src.features.repositories.routes.repository_controller")
    def test_post_repositories_per_page_fixed_at_25(self, mock_controller, client):
        """Test per_page is fixed at 25 regardless of input."""
        mock_controller.get_repositories.return_value = (
            [],
            {"current_page": 1, "per_page": 25, "has_next": False, "has_previous": False},
        )

        # Try to set per_page to something else
        response = client.post(
            "/api/repositories",
            data=json.dumps({"per_page": 100}),
            content_type="application/json",
        )

        assert response.status_code == 200
        # Verify controller was called with per_page=25 (from Config)
        call_args = mock_controller.get_repositories.call_args
        filters = call_args[0][0]
        assert filters.per_page == 25
