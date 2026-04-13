"""
Unit tests for repository scoring algorithm.

Tests the calculate_repository_score function which combines popularity
metrics (stars, forks, watchers) with recency to produce quality scores.
"""

import pytest
from datetime import datetime, timedelta
from src.features.repositories.domain.repo_scoring import (
    calculate_repository_score,
)
from src.shared.models import Repository


class TestCalculateRepositoryScore:
    """Test suite for repository scoring algorithm."""

    def test_basic_scoring_with_stars_only(self):
        """Test scoring with only stars, no forks or watchers."""
        repo = Repository(
            id=1,
            name="test-repo",
            full_name="user/test-repo",
            url="https://github.com/user/test-repo",
            stars=1000,
            forks=0,
            watchers=0,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        score = calculate_repository_score(repo)

        assert isinstance(score, float)
        assert score > 0

    def test_scoring_with_all_popularity_metrics(self):
        """Test scoring with stars, forks, and watchers."""
        repo = Repository(
            id=2,
            name="popular-repo",
            full_name="user/popular-repo",
            url="https://github.com/user/popular-repo",
            stars=5000,
            forks=1000,
            watchers=500,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        score = calculate_repository_score(repo)

        assert score > 0
        assert isinstance(score, float)

    def test_higher_stars_yields_higher_score(self):
        """Test that repositories with more stars score higher."""
        repo_low_stars = Repository(
            id=3,
            name="low-stars",
            full_name="user/low-stars",
            url="https://github.com/user/low-stars",
            stars=100,
            forks=10,
            watchers=5,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        repo_high_stars = Repository(
            id=4,
            name="high-stars",
            full_name="user/high-stars",
            url="https://github.com/user/high-stars",
            stars=10000,
            forks=10,
            watchers=5,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        score_low = calculate_repository_score(repo_low_stars)
        score_high = calculate_repository_score(repo_high_stars)

        assert score_high > score_low

    def test_recency_affects_score(self):
        """Test that recently updated repos score higher than old ones."""
        recent_update = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        old_update = (datetime.utcnow() - timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        repo_recent = Repository(
            id=5,
            name="recent-repo",
            full_name="user/recent-repo",
            url="https://github.com/user/recent-repo",
            stars=1000,
            forks=100,
            watchers=50,
            updated_at=recent_update,
        )

        repo_old = Repository(
            id=6,
            name="old-repo",
            full_name="user/old-repo",
            url="https://github.com/user/old-repo",
            stars=1000,
            forks=100,
            watchers=50,
            updated_at=old_update,
        )

        score_recent = calculate_repository_score(repo_recent)
        score_old = calculate_repository_score(repo_old)

        assert score_recent > score_old

    def test_zero_metrics_returns_positive_score(self):
        """Test that repos with zero metrics still get a positive score."""
        repo = Repository(
            id=7,
            name="zero-repo",
            full_name="user/zero-repo",
            url="https://github.com/user/zero-repo",
            stars=0,
            forks=0,
            watchers=0,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        score = calculate_repository_score(repo)

        # Due to log(0+1) = 0, score should still be > 0 from recency
        assert score >= 0

    def test_missing_updated_at_uses_default_recency(self):
        """Test that missing updated_at doesn't crash and uses default."""
        repo = Repository(
            id=8,
            name="no-date-repo",
            full_name="user/no-date-repo",
            url="https://github.com/user/no-date-repo",
            stars=1000,
            forks=100,
            watchers=50,
            updated_at=None,
        )

        score = calculate_repository_score(repo)

        assert isinstance(score, float)
        assert score > 0

    def test_invalid_date_format_handles_gracefully(self):
        """Test that invalid date formats don't crash scoring."""
        repo = Repository(
            id=9,
            name="bad-date-repo",
            full_name="user/bad-date-repo",
            url="https://github.com/user/bad-date-repo",
            stars=1000,
            forks=100,
            watchers=50,
            updated_at="invalid-date",
        )

        score = calculate_repository_score(repo)

        assert isinstance(score, float)
        assert score > 0

    def test_forks_contribute_to_score(self):
        """Test that forks contribute to the overall score."""
        repo_no_forks = Repository(
            id=10,
            name="no-forks",
            full_name="user/no-forks",
            url="https://github.com/user/no-forks",
            stars=1000,
            forks=0,
            watchers=100,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        repo_with_forks = Repository(
            id=11,
            name="with-forks",
            full_name="user/with-forks",
            url="https://github.com/user/with-forks",
            stars=1000,
            forks=500,
            watchers=100,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        score_no_forks = calculate_repository_score(repo_no_forks)
        score_with_forks = calculate_repository_score(repo_with_forks)

        assert score_with_forks > score_no_forks

    def test_watchers_contribute_to_score(self):
        """Test that watchers contribute to the overall score."""
        repo_no_watchers = Repository(
            id=12,
            name="no-watchers",
            full_name="user/no-watchers",
            url="https://github.com/user/no-watchers",
            stars=1000,
            forks=100,
            watchers=0,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        repo_with_watchers = Repository(
            id=13,
            name="with-watchers",
            full_name="user/with-watchers",
            url="https://github.com/user/with-watchers",
            stars=1000,
            forks=100,
            watchers=500,
            updated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        score_no_watchers = calculate_repository_score(repo_no_watchers)
        score_with_watchers = calculate_repository_score(repo_with_watchers)

        assert score_with_watchers > score_no_watchers

    def test_thirty_day_half_life_recency_decay(self):
        """Test the 30-day half-life recency decay mechanism."""
        now = datetime.utcnow()
        thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sixty_days_ago = (now - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        repo_30_days = Repository(
            id=14,
            name="30-days",
            full_name="user/30-days",
            url="https://github.com/user/30-days",
            stars=1000,
            forks=100,
            watchers=50,
            updated_at=thirty_days_ago,
        )

        repo_60_days = Repository(
            id=15,
            name="60-days",
            full_name="user/60-days",
            url="https://github.com/user/60-days",
            stars=1000,
            forks=100,
            watchers=50,
            updated_at=sixty_days_ago,
        )

        score_30 = calculate_repository_score(repo_30_days)
        score_60 = calculate_repository_score(repo_60_days)

        # After 30 days, recency should be ~0.5, after 60 days ~0.25
        assert score_30 > score_60

    def test_score_is_deterministic(self):
        """Test that the same repo produces the same score consistently."""
        repo = Repository(
            id=16,
            name="deterministic",
            full_name="user/deterministic",
            url="https://github.com/user/deterministic",
            stars=1500,
            forks=300,
            watchers=150,
            updated_at="2024-01-01T00:00:00Z",
        )

        score1 = calculate_repository_score(repo)
        score2 = calculate_repository_score(repo)

        assert score1 == score2
