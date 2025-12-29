"""
Integration tests for the Froglol application.
These tests exercise the entire application stack including routes, services, and models.
"""

import pytest
from app import db
from app.models import Bookmark, Alias


@pytest.fixture
def seeded_app(app):
    """Create an app with a realistic set of bookmarks."""
    with app.app_context():
        # Create common bookmarks similar to seed data
        bookmarks = [
            Bookmark(
                name="manage",
                url="http://localhost:5000/manage",
                description="Manage bookmarks",
                use_count=0,
            ),
            Bookmark(
                name="google",
                url="https://www.google.com/search?q=%s",
                description="Google Search",
                use_count=50,
            ),
            Bookmark(
                name="github",
                url="https://github.com/search?q=%s",
                description="GitHub Search",
                use_count=30,
            ),
            Bookmark(
                name="youtube",
                url="https://www.youtube.com/results?search_query=%s",
                description="YouTube Search",
                use_count=20,
            ),
            Bookmark(
                name="stackoverflow",
                url="https://stackoverflow.com/search?q=%s",
                description="Stack Overflow",
                use_count=40,
            ),
            Bookmark(
                name="chatgpt",
                url="https://chat.openai.com/",
                description="ChatGPT",
                use_count=15,
            ),
        ]

        for bookmark in bookmarks:
            db.session.add(bookmark)
        db.session.commit()

        # Add aliases
        aliases = [
            Alias(alias="g", bookmark_id=bookmarks[1].id),  # google
            Alias(alias="search", bookmark_id=bookmarks[1].id),  # google
            Alias(alias="gh", bookmark_id=bookmarks[2].id),  # github
            Alias(alias="yt", bookmark_id=bookmarks[3].id),  # youtube
            Alias(alias="so", bookmark_id=bookmarks[4].id),  # stackoverflow
            Alias(alias="gpt", bookmark_id=bookmarks[5].id),  # chatgpt
        ]

        for alias in aliases:
            db.session.add(alias)
        db.session.commit()

        yield app


@pytest.fixture
def seeded_client(seeded_app):
    """Create a client with seeded data."""
    return seeded_app.test_client()


class TestEndToEndRedirectFlow:
    """Test complete redirect workflows from query to response."""

    def test_exact_bookmark_redirect(self, seeded_client):
        """Test redirecting to an exact bookmark match."""
        response = seeded_client.get("/?q=google python tutorial")
        assert response.status_code == 302
        assert "google.com/search" in response.location
        assert "python+tutorial" in response.location

    def test_alias_redirect(self, seeded_client):
        """Test redirecting via an alias."""
        response = seeded_client.get("/?q=g flask framework")
        assert response.status_code == 302
        assert "google.com/search" in response.location
        assert "flask+framework" in response.location

    def test_no_args_redirect(self, seeded_client):
        """Test redirecting to a bookmark without arguments."""
        response = seeded_client.get("/?q=chatgpt")
        assert response.status_code == 302
        assert "chat.openai.com" in response.location

    def test_no_match(self, seeded_client):
        """Test that no match returns 404."""
        response = seeded_client.get("/?q=completelyrandomcommand test")
        assert response.status_code == 404

    def test_empty_query(self, seeded_client):
        """Test handling of empty query."""
        response = seeded_client.get("/")
        assert response.status_code == 404

    def test_special_characters_in_args(self, seeded_client):
        """Test proper encoding of special characters."""
        # Use URL encoding for the query parameter to include special characters
        from urllib.parse import quote

        query = quote("google test&special=value")
        response = seeded_client.get(f"/?q={query}")
        assert response.status_code == 302
        # Special characters should be URL encoded in the redirect
        assert "test%26special%3Dvalue" in response.location

    def test_multiple_word_command_search(self, seeded_client):
        """Test searching with multiple words."""
        response = seeded_client.get("/?q=stackoverflow how to fix error")
        assert response.status_code == 302
        assert "stackoverflow.com" in response.location
        assert "how+to+fix+error" in response.location


class TestUsageTracking:
    """Test that usage counts are properly tracked."""

    def test_usage_increments_on_redirect(self, seeded_client, seeded_app):
        """Test that redirecting increments usage count."""
        with seeded_app.app_context():
            initial_count = Bookmark.query.filter_by(name="google").first().use_count

        # Use the bookmark
        response = seeded_client.get("/?q=google test")
        assert response.status_code == 302

        with seeded_app.app_context():
            final_count = Bookmark.query.filter_by(name="google").first().use_count
            assert final_count == initial_count + 1

    def test_usage_increments_via_alias(self, seeded_client, seeded_app):
        """Test that using an alias increments the parent bookmark's count."""
        with seeded_app.app_context():
            initial_count = Bookmark.query.filter_by(name="google").first().use_count

        # Use via alias
        response = seeded_client.get("/?q=g test")
        assert response.status_code == 302

        with seeded_app.app_context():
            final_count = Bookmark.query.filter_by(name="google").first().use_count
            assert final_count == initial_count + 1

    def test_usage_not_incremented_on_no_match(self, seeded_client, seeded_app):
        """Test that failed lookups don't increment any counts."""
        with seeded_app.app_context():
            initial_counts = {b.name: b.use_count for b in Bookmark.query.all()}

        # Query that doesn't match
        response = seeded_client.get("/?q=nonexistent test")
        assert response.status_code == 404

        with seeded_app.app_context():
            final_counts = {b.name: b.use_count for b in Bookmark.query.all()}
            # All counts should be unchanged
            assert initial_counts == final_counts


class TestBookmarkCRUDIntegration:
    """Test complete CRUD workflows for bookmarks."""

    def test_create_and_use_bookmark(self, client, app):
        """Test creating a bookmark and immediately using it."""
        # Create bookmark
        response = client.post(
            "/api/bookmarks",
            json={
                "name": "reddit",
                "url": "https://www.reddit.com/search?q=%s",
                "description": "Reddit Search",
            },
        )
        assert response.status_code == 201

        # Use it immediately
        response = client.get("/?q=reddit python")
        assert response.status_code == 302
        assert "reddit.com" in response.location
        assert "python" in response.location

    def test_create_with_alias_and_use_alias(self, client):
        """Test creating a bookmark with aliases and using them."""
        # Create with aliases
        response = client.post(
            "/api/bookmarks",
            json={
                "name": "twitter",
                "url": "https://twitter.com/search?q=%s",
                "description": "Twitter Search",
                "aliases": ["tw", "x"],
            },
        )
        assert response.status_code == 201

        # Use via alias
        response = client.get("/?q=tw elon musk")
        assert response.status_code == 302
        assert "twitter.com" in response.location

        # Use via another alias
        response = client.get("/?q=x spacex")
        assert response.status_code == 302
        assert "twitter.com" in response.location

    def test_update_bookmark_url_affects_redirects(self, client, app):
        """Test that updating a bookmark URL changes redirect behavior."""
        # Create bookmark
        response = client.post(
            "/api/bookmarks",
            json={"name": "test", "url": "https://example.com?q=%s"},
        )
        assert response.status_code == 201
        bookmark_id = response.get_json()["id"]

        # Use it
        response = client.get("/?q=test hello")
        assert response.status_code == 302
        assert "example.com" in response.location

        # Update the URL
        response = client.put(
            f"/api/bookmarks/{bookmark_id}",
            json={"url": "https://updated.com?search=%s"},
        )
        assert response.status_code == 200

        # Use it again - should redirect to new URL
        response = client.get("/?q=test hello")
        assert response.status_code == 302
        assert "updated.com" in response.location

    def test_delete_bookmark_prevents_redirect(self, client, app):
        """Test that deleting a bookmark prevents future redirects."""
        # Create bookmark
        response = client.post(
            "/api/bookmarks",
            json={"name": "temp", "url": "https://example.com"},
        )
        assert response.status_code == 201
        bookmark_id = response.get_json()["id"]

        # Verify it works
        response = client.get("/?q=temp")
        assert response.status_code == 302
        assert "example.com" in response.location

        # Delete it
        response = client.delete(f"/api/bookmarks/{bookmark_id}")
        assert response.status_code == 204

        # Try to use it - should return 404
        response = client.get("/?q=temp")
        assert response.status_code == 404

    def test_add_alias_after_creation(self, client, app):
        """Test adding an alias to an existing bookmark and using it."""
        # Create bookmark
        response = client.post(
            "/api/bookmarks",
            json={"name": "wiki", "url": "https://wikipedia.org/wiki/%s"},
        )
        assert response.status_code == 201
        bookmark_id = response.get_json()["id"]

        # Add alias
        response = client.post(
            f"/api/bookmarks/{bookmark_id}/aliases",
            json={"alias": "w"},
        )
        assert response.status_code == 201

        # Use via alias
        response = client.get("/?q=w python")
        assert response.status_code == 302
        assert "wikipedia.org" in response.location


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_case_insensitive_matching(self, seeded_client):
        """Test that command matching is case-insensitive."""
        # All these should work
        for query in ["GOOGLE test", "Google test", "google test", "gOoGlE test"]:
            response = seeded_client.get(f"/?q={query}")
            assert response.status_code == 302
            assert "google.com" in response.location

    def test_whitespace_handling(self, seeded_client):
        """Test various whitespace scenarios."""
        # Multiple spaces between command and args
        response = seeded_client.get("/?q=google   multiple   spaces")
        assert response.status_code == 302
        assert "google.com" in response.location

        # Leading/trailing whitespace
        response = seeded_client.get("/?q=  google  test  ")
        assert response.status_code == 302
        assert "google.com" in response.location

    def test_url_without_placeholder(self, client):
        """Test bookmarks without %s placeholder."""
        # Create bookmark without %s
        response = client.post(
            "/api/bookmarks",
            json={"name": "homepage", "url": "https://example.com"},
        )
        assert response.status_code == 201

        # Use it with args (args should be ignored/appended as empty)
        response = client.get("/?q=homepage ignored args")
        assert response.status_code == 302
        assert "example.com" in response.location

    def test_unicode_in_query(self, seeded_client):
        """Test handling of Unicode characters."""
        response = seeded_client.get("/?q=google 你好世界")
        assert response.status_code == 302
        assert "google.com" in response.location
        # Unicode should be URL encoded

    def test_very_long_query(self, seeded_client):
        """Test handling of very long queries."""
        long_query = "google " + "test " * 100
        response = seeded_client.get(f"/?q={long_query}")
        assert response.status_code == 302
        assert "google.com" in response.location


class TestConcurrentUsage:
    """Test scenarios with multiple operations."""

    def test_multiple_redirects_increment_correctly(self, seeded_client, seeded_app):
        """Test that multiple redirects increment count correctly."""
        with seeded_app.app_context():
            initial_count = Bookmark.query.filter_by(name="google").first().use_count

        # Make multiple requests
        for _ in range(5):
            response = seeded_client.get("/?q=google test")
            assert response.status_code == 302

        with seeded_app.app_context():
            final_count = Bookmark.query.filter_by(name="google").first().use_count
            assert final_count == initial_count + 5

    def test_interleaved_api_and_redirect_operations(self, client, app):
        """Test mixing API operations with redirects."""
        # Create a bookmark
        response = client.post(
            "/api/bookmarks",
            json={"name": "test1", "url": "https://example1.com?q=%s"},
        )
        assert response.status_code == 201
        bookmark_id = response.get_json()["id"]

        # Use it
        response = client.get("/?q=test1 hello")
        assert response.status_code == 302

        # Update it
        response = client.put(
            f"/api/bookmarks/{bookmark_id}",
            json={"url": "https://example2.com?q=%s"},
        )
        assert response.status_code == 200

        # Use it again
        response = client.get("/?q=test1 world")
        assert response.status_code == 302
        assert "example2.com" in response.location

        # Delete it
        response = client.delete(f"/api/bookmarks/{bookmark_id}")
        assert response.status_code == 204

        # Try to use it - should return 404
        response = client.get("/?q=test1 fail")
        assert response.status_code == 404
