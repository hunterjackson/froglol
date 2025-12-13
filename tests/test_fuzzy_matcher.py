import pytest
from app.services.fuzzy_matcher import FuzzyMatcher
from app.models import Bookmark, Alias
from app import db


@pytest.fixture
def multiple_bookmarks(app):
    """Create multiple bookmarks for fuzzy matching tests."""
    with app.app_context():
        bookmarks = [
            Bookmark(name='google', url='https://google.com/search?q=%s', description='Google search', use_count=100),
            Bookmark(name='github', url='https://github.com/search?q=%s', description='GitHub search', use_count=50),
            Bookmark(name='gitlab', url='https://gitlab.com/search?q=%s', description='GitLab search', use_count=10),
            Bookmark(name='stackoverflow', url='https://stackoverflow.com/search?q=%s', description='Stack Overflow', use_count=75),
        ]

        for bookmark in bookmarks:
            db.session.add(bookmark)
        db.session.commit()

        # Add some aliases
        aliases = [
            Alias(alias='g', bookmark_id=bookmarks[0].id),
            Alias(alias='gh', bookmark_id=bookmarks[1].id),
            Alias(alias='so', bookmark_id=bookmarks[3].id),
        ]

        for alias in aliases:
            db.session.add(alias)
        db.session.commit()

        return bookmarks


def test_fuzzy_matcher_exact_match(app, multiple_bookmarks):
    """Test fuzzy matching with exact match."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=60, limit=3)
        results = matcher.find_similar_commands('google')

        assert len(results) > 0
        assert results[0]['name'] == 'google'
        assert results[0]['score'] == 100  # Exact match


def test_fuzzy_matcher_close_match(app, multiple_bookmarks):
    """Test fuzzy matching with typos."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=60, limit=3)
        results = matcher.find_similar_commands('googl')

        assert len(results) > 0
        assert results[0]['name'] == 'google'
        assert results[0]['score'] >= 60


def test_fuzzy_matcher_multiple_results(app, multiple_bookmarks):
    """Test fuzzy matching returns multiple similar results."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=50, limit=3)
        results = matcher.find_similar_commands('git')

        # Should match both github and gitlab
        assert len(results) >= 2
        names = [r['name'] for r in results]
        assert 'github' in names or 'gh' in names
        assert 'gitlab' in names


def test_fuzzy_matcher_respects_limit(app, multiple_bookmarks):
    """Test fuzzy matching respects the limit parameter."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=30, limit=2)
        results = matcher.find_similar_commands('g')

        assert len(results) <= 2


def test_fuzzy_matcher_threshold(app, multiple_bookmarks):
    """Test fuzzy matching respects threshold."""
    with app.app_context():
        # High threshold - should match only very similar
        matcher = FuzzyMatcher(threshold=90, limit=5)
        results = matcher.find_similar_commands('googl')

        # Should only get google, not other bookmarks
        assert len(results) <= 2  # google and possibly alias 'g'

        # Low threshold - should match more
        matcher = FuzzyMatcher(threshold=30, limit=5)
        results = matcher.find_similar_commands('g')

        assert len(results) >= 2


def test_fuzzy_matcher_no_results(app, multiple_bookmarks):
    """Test fuzzy matching with no matches."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=80, limit=3)
        results = matcher.find_similar_commands('zzzzzzz')

        assert len(results) == 0


def test_fuzzy_matcher_empty_database(app):
    """Test fuzzy matching with empty database."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=60, limit=3)
        results = matcher.find_similar_commands('test')

        assert results == []


def test_fuzzy_matcher_case_insensitive(app, multiple_bookmarks):
    """Test fuzzy matching is case insensitive."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=60, limit=3)

        results_lower = matcher.find_similar_commands('google')
        results_upper = matcher.find_similar_commands('GOOGLE')
        results_mixed = matcher.find_similar_commands('GoOgLe')

        assert results_lower[0]['name'] == results_upper[0]['name']
        assert results_lower[0]['name'] == results_mixed[0]['name']


def test_fuzzy_matcher_includes_aliases(app, multiple_bookmarks):
    """Test fuzzy matching includes aliases."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=60, limit=3)
        results = matcher.find_similar_commands('gh')

        # Should match the 'gh' alias for github
        assert len(results) > 0
        # The result should point to the github bookmark
        assert any(r['name'] == 'gh' for r in results)


def test_fuzzy_matcher_deduplication(app, multiple_bookmarks):
    """Test fuzzy matching deduplicates by bookmark_id."""
    with app.app_context():
        # Query that matches both 'google' and its alias 'g'
        matcher = FuzzyMatcher(threshold=50, limit=5)
        results = matcher.find_similar_commands('g')

        # Count unique bookmark IDs
        bookmark_ids = [r['bookmark_id'] for r in results]
        unique_ids = set(bookmark_ids)

        # Should have no duplicate bookmark_ids
        assert len(bookmark_ids) == len(unique_ids)


def test_fuzzy_matcher_sorting(app, multiple_bookmarks):
    """Test fuzzy matching sorts by score then use_count."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=30, limit=5)
        results = matcher.find_similar_commands('g')

        # Results should be sorted by score (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]['score'] >= results[i + 1]['score']

                # If scores are equal, should be sorted by use_count
                if results[i]['score'] == results[i + 1]['score']:
                    assert results[i]['use_count'] >= results[i + 1]['use_count']


def test_fuzzy_matcher_returns_correct_fields(app, multiple_bookmarks):
    """Test fuzzy matching returns all expected fields."""
    with app.app_context():
        matcher = FuzzyMatcher(threshold=60, limit=3)
        results = matcher.find_similar_commands('google')

        assert len(results) > 0
        result = results[0]

        # Check all expected fields are present
        assert 'name' in result
        assert 'url' in result
        assert 'description' in result
        assert 'score' in result
        assert 'use_count' in result
        assert 'bookmark_id' in result

        # Verify types
        assert isinstance(result['score'], (int, float))
        assert isinstance(result['use_count'], int)
        assert isinstance(result['bookmark_id'], int)
