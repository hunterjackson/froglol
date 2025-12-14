"""
Unit tests for individual components and functions.
These tests focus on testing single functions/methods in isolation.
"""

import pytest
from app.models import Bookmark, Alias
from app import db
from app.services.redirect_service import (
    parse_query,
    substitute_args,
    find_bookmark_by_name_or_alias,
    increment_usage,
    process_redirect,
)
from app.services.fuzzy_matcher import FuzzyMatcher


class TestParseQuery:
    """Unit tests for parse_query function."""

    def test_parse_command_with_args(self):
        """Test parsing command with arguments."""
        command, args = parse_query("google hello world")
        assert command == "google"
        assert args == "hello world"

    def test_parse_command_without_args(self):
        """Test parsing command without arguments."""
        command, args = parse_query("google")
        assert command == "google"
        assert args == ""

    def test_parse_empty_query(self):
        """Test parsing empty query."""
        command, args = parse_query("")
        assert command == ""
        assert args == ""

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only query."""
        command, args = parse_query("   ")
        assert command == ""
        assert args == ""

    def test_parse_normalizes_case(self):
        """Test that command is normalized to lowercase."""
        command, args = parse_query("GOOGLE Test")
        assert command == "google"
        assert args == "Test"  # Args preserve case

    def test_parse_multiple_spaces(self):
        """Test parsing with multiple spaces."""
        command, args = parse_query("google   hello   world")
        assert command == "google"
        assert args == "hello   world"  # Preserves spacing in args

    def test_parse_leading_trailing_spaces(self):
        """Test parsing with leading/trailing spaces."""
        command, args = parse_query("  google  hello  ")
        assert command == "google"
        assert args == "hello"  # strip() removes trailing spaces from the whole query

    def test_parse_single_word(self):
        """Test parsing a single word."""
        command, args = parse_query("test")
        assert command == "test"
        assert args == ""

    def test_parse_special_characters_in_command(self):
        """Test parsing with special characters."""
        command, args = parse_query("test-command hello")
        assert command == "test-command"
        assert args == "hello"


class TestSubstituteArgs:
    """Unit tests for substitute_args function."""

    def test_substitute_basic(self):
        """Test basic substitution."""
        url = substitute_args("https://example.com?q=%s", "test")
        assert url == "https://example.com?q=test"

    def test_substitute_empty_args(self):
        """Test substitution with empty args."""
        url = substitute_args("https://example.com?q=%s", "")
        assert url == "https://example.com?q="

    def test_substitute_no_placeholder(self):
        """Test URL without %s placeholder."""
        url = substitute_args("https://example.com", "test")
        assert url == "https://example.com"

    def test_substitute_url_encoding_spaces(self):
        """Test URL encoding of spaces."""
        url = substitute_args("https://example.com?q=%s", "hello world")
        assert url == "https://example.com?q=hello+world"

    def test_substitute_url_encoding_special_chars(self):
        """Test URL encoding of special characters."""
        url = substitute_args("https://example.com?q=%s", "test&value=1")
        assert url == "https://example.com?q=test%26value%3D1"

    def test_substitute_multiple_placeholders(self):
        """Test multiple %s placeholders (all get replaced)."""
        url = substitute_args("https://example.com?q=%s&search=%s", "test")
        assert url == "https://example.com?q=test&search=test"

    def test_substitute_unicode(self):
        """Test substitution with Unicode characters."""
        url = substitute_args("https://example.com?q=%s", "你好")
        # Should be URL encoded
        assert "example.com" in url
        assert "%s" not in url

    def test_substitute_plus_sign(self):
        """Test encoding of + sign."""
        url = substitute_args("https://example.com?q=%s", "C++")
        assert "%2B" in url or "C%2B%2B" in url


class TestFindBookmarkByNameOrAlias:
    """Unit tests for find_bookmark_by_name_or_alias function."""

    def test_find_by_exact_name(self, app):
        """Test finding bookmark by exact name."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            result = find_bookmark_by_name_or_alias("test")
            assert result is not None
            assert result.name == "test"

    def test_find_by_alias(self, app):
        """Test finding bookmark by alias."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            alias = Alias(alias="t", bookmark_id=bookmark.id)
            db.session.add(alias)
            db.session.commit()

            result = find_bookmark_by_name_or_alias("t")
            assert result is not None
            assert result.name == "test"

    def test_find_nonexistent(self, app):
        """Test finding nonexistent bookmark."""
        with app.app_context():
            result = find_bookmark_by_name_or_alias("nonexistent")
            assert result is None

    def test_find_case_sensitive(self, app):
        """Test that search is case-sensitive (lowercase expected)."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            # Should find lowercase
            result = find_bookmark_by_name_or_alias("test")
            assert result is not None

            # Should NOT find uppercase (case-sensitive)
            result = find_bookmark_by_name_or_alias("TEST")
            assert result is None

    def test_find_prefers_name_over_alias(self, app):
        """Test that name match is preferred over alias."""
        with app.app_context():
            bookmark1 = Bookmark(name="test", url="https://example1.com")
            bookmark2 = Bookmark(name="other", url="https://example2.com")
            db.session.add(bookmark1)
            db.session.add(bookmark2)
            db.session.commit()

            # Create alias that matches bookmark1's name
            alias = Alias(alias="test", bookmark_id=bookmark2.id)
            db.session.add(alias)
            db.session.commit()

            result = find_bookmark_by_name_or_alias("test")
            # Should find bookmark1 (name match), not bookmark2 (alias match)
            assert result.url == "https://example1.com"


class TestIncrementUsage:
    """Unit tests for increment_usage function."""

    def test_increment_from_zero(self, app):
        """Test incrementing from zero."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com", use_count=0)
            db.session.add(bookmark)
            db.session.commit()
            bookmark_id = bookmark.id

            # Reload to get fresh instance
            bookmark = Bookmark.query.get(bookmark_id)
            increment_usage(bookmark)

            # Verify
            bookmark = Bookmark.query.get(bookmark_id)
            assert bookmark.use_count == 1

    def test_increment_multiple_times(self, app):
        """Test incrementing multiple times."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com", use_count=0)
            db.session.add(bookmark)
            db.session.commit()
            bookmark_id = bookmark.id

            for i in range(5):
                bookmark = Bookmark.query.get(bookmark_id)
                increment_usage(bookmark)

            bookmark = Bookmark.query.get(bookmark_id)
            assert bookmark.use_count == 5

    def test_increment_persists(self, app):
        """Test that increment persists to database."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com", use_count=0)
            db.session.add(bookmark)
            db.session.commit()
            bookmark_id = bookmark.id

        # Increment in one context
        with app.app_context():
            bookmark = Bookmark.query.get(bookmark_id)
            increment_usage(bookmark)

        # Verify in another context
        with app.app_context():
            bookmark = Bookmark.query.get(bookmark_id)
            assert bookmark.use_count == 1


class TestProcessRedirect:
    """Unit tests for process_redirect function."""

    def test_process_exact_match(self, app):
        """Test processing exact match."""
        with app.app_context():
            bookmark = Bookmark(
                name="google", url="https://google.com/search?q=%s"
            )
            db.session.add(bookmark)
            db.session.commit()

            result = process_redirect("google test")
            assert result.url is not None
            assert "google.com" in result.url
            assert "test" in result.url
            assert result.suggestions is None

    def test_process_empty_query(self, app):
        """Test processing empty query."""
        with app.app_context():
            result = process_redirect("")
            assert result.url is not None
            # Should return fallback URL

    def test_process_no_match_no_fuzzy(self, app):
        """Test processing with no match and no fuzzy matcher."""
        with app.app_context():
            result = process_redirect("nonexistent test", fuzzy_matcher=None)
            assert result.url is not None
            # Should fallback with full query

    def test_process_no_match_with_fuzzy(self, app):
        """Test processing with no match but fuzzy suggestions."""
        with app.app_context():
            bookmark = Bookmark(name="google", url="https://google.com/search?q=%s")
            db.session.add(bookmark)
            db.session.commit()

            fuzzy_matcher = FuzzyMatcher(threshold=60, limit=3)
            result = process_redirect("googl test", fuzzy_matcher=fuzzy_matcher)

            # Should return suggestions for "googl"
            assert result.suggestions is not None
            assert len(result.suggestions) > 0
            assert result.url is None

    def test_process_custom_fallback(self, app):
        """Test processing with custom fallback URL."""
        with app.app_context():
            custom_fallback = "https://duckduckgo.com/?q=%s"
            result = process_redirect(
                "nonexistent test",
                fuzzy_matcher=None,
                default_fallback_url=custom_fallback,
            )
            assert result.url is not None
            assert "duckduckgo.com" in result.url

    def test_process_increments_usage(self, app):
        """Test that process_redirect increments usage."""
        with app.app_context():
            bookmark = Bookmark(
                name="test", url="https://example.com", use_count=0
            )
            db.session.add(bookmark)
            db.session.commit()
            bookmark_id = bookmark.id

            result = process_redirect("test")
            assert result.url is not None

            bookmark = Bookmark.query.get(bookmark_id)
            assert bookmark.use_count == 1


class TestBookmarkModel:
    """Unit tests for Bookmark model."""

    def test_create_bookmark(self, app):
        """Test creating a bookmark."""
        with app.app_context():
            bookmark = Bookmark(
                name="test",
                url="https://example.com",
                description="Test bookmark",
            )
            db.session.add(bookmark)
            db.session.commit()

            assert bookmark.id is not None
            assert bookmark.use_count == 0  # Default value

    def test_bookmark_defaults(self, app):
        """Test bookmark default values."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            assert bookmark.description is None
            assert bookmark.use_count == 0

    def test_bookmark_unique_name(self, app):
        """Test that bookmark names must be unique."""
        with app.app_context():
            bookmark1 = Bookmark(name="test", url="https://example1.com")
            db.session.add(bookmark1)
            db.session.commit()

            bookmark2 = Bookmark(name="test", url="https://example2.com")
            db.session.add(bookmark2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_bookmark_to_dict(self, app):
        """Test bookmark serialization."""
        with app.app_context():
            bookmark = Bookmark(
                name="test",
                url="https://example.com",
                description="Test",
            )
            db.session.add(bookmark)
            db.session.commit()

            data = bookmark.to_dict()
            assert data["name"] == "test"
            assert data["url"] == "https://example.com"
            assert data["description"] == "Test"
            assert data["use_count"] == 0
            assert "id" in data
            assert "aliases" in data


class TestAliasModel:
    """Unit tests for Alias model."""

    def test_create_alias(self, app):
        """Test creating an alias."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            alias = Alias(alias="t", bookmark_id=bookmark.id)
            db.session.add(alias)
            db.session.commit()

            assert alias.id is not None
            assert alias.bookmark.name == "test"

    def test_alias_unique(self, app):
        """Test that aliases must be unique."""
        with app.app_context():
            bookmark1 = Bookmark(name="test1", url="https://example1.com")
            bookmark2 = Bookmark(name="test2", url="https://example2.com")
            db.session.add_all([bookmark1, bookmark2])
            db.session.commit()

            alias1 = Alias(alias="t", bookmark_id=bookmark1.id)
            db.session.add(alias1)
            db.session.commit()

            alias2 = Alias(alias="t", bookmark_id=bookmark2.id)
            db.session.add(alias2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_alias_cascade_delete(self, app):
        """Test that aliases are deleted when bookmark is deleted."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            alias = Alias(alias="t", bookmark_id=bookmark.id)
            db.session.add(alias)
            db.session.commit()

            alias_id = alias.id
            bookmark_id = bookmark.id

            # Delete bookmark
            db.session.delete(bookmark)
            db.session.commit()

            # Alias should be deleted
            assert Alias.query.get(alias_id) is None
            assert Bookmark.query.get(bookmark_id) is None

    def test_alias_relationship(self, app):
        """Test alias-bookmark relationship."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            alias1 = Alias(alias="t", bookmark_id=bookmark.id)
            alias2 = Alias(alias="tst", bookmark_id=bookmark.id)
            db.session.add_all([alias1, alias2])
            db.session.commit()

            # Access from bookmark side
            bookmark = Bookmark.query.filter_by(name="test").first()
            assert len(bookmark.aliases) == 2
            alias_values = {a.alias for a in bookmark.aliases}
            assert alias_values == {"t", "tst"}

    def test_alias_to_dict(self, app):
        """Test alias serialization."""
        with app.app_context():
            bookmark = Bookmark(name="test", url="https://example.com")
            db.session.add(bookmark)
            db.session.commit()

            alias = Alias(alias="t", bookmark_id=bookmark.id)
            db.session.add(alias)
            db.session.commit()

            data = alias.to_dict()
            assert data["alias"] == "t"
            assert "id" in data
            assert "bookmark_id" in data


class TestFuzzyMatcherUnit:
    """Unit tests for FuzzyMatcher class."""

    def test_fuzzy_matcher_initialization(self):
        """Test FuzzyMatcher initialization."""
        matcher = FuzzyMatcher(threshold=70, limit=5)
        assert matcher.threshold == 70
        assert matcher.limit == 5

    def test_fuzzy_matcher_default_values(self):
        """Test FuzzyMatcher default values."""
        matcher = FuzzyMatcher()
        assert matcher.threshold == 60
        assert matcher.limit == 3

    def test_fuzzy_matcher_empty_database(self, app):
        """Test fuzzy matcher with empty database."""
        with app.app_context():
            matcher = FuzzyMatcher(threshold=60, limit=3)
            results = matcher.find_similar_commands("test")
            assert results == []

    def test_fuzzy_matcher_invalid_threshold(self):
        """Test that matcher handles invalid threshold values."""
        # Should accept any numeric value (no validation)
        matcher = FuzzyMatcher(threshold=150, limit=3)
        assert matcher.threshold == 150

        matcher = FuzzyMatcher(threshold=-10, limit=3)
        assert matcher.threshold == -10

    def test_fuzzy_matcher_invalid_limit(self):
        """Test that matcher handles invalid limit values."""
        matcher = FuzzyMatcher(threshold=60, limit=0)
        assert matcher.limit == 0

        matcher = FuzzyMatcher(threshold=60, limit=-1)
        assert matcher.limit == -1
