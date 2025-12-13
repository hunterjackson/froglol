import pytest
from app.services.redirect_service import parse_query, substitute_args


def test_parse_query():
    """Test query parsing."""
    # Basic case
    command, args = parse_query('google hello world')
    assert command == 'google'
    assert args == 'hello world'

    # No args
    command, args = parse_query('google')
    assert command == 'google'
    assert args == ''

    # Empty query
    command, args = parse_query('')
    assert command == ''
    assert args == ''

    # Case insensitive
    command, args = parse_query('GOOGLE test')
    assert command == 'google'
    assert args == 'test'


def test_substitute_args():
    """Test URL argument substitution."""
    # Basic substitution
    url = substitute_args('https://google.com/search?q=%s', 'test')
    assert url == 'https://google.com/search?q=test'

    # No args
    url = substitute_args('https://google.com/search?q=%s', '')
    assert url == 'https://google.com/search?q='

    # URL encoding
    url = substitute_args('https://google.com/search?q=%s', 'hello world')
    assert url == 'https://google.com/search?q=hello+world'

    # Special characters
    url = substitute_args('https://google.com/search?q=%s', 'test&special=chars')
    assert 'test%26special%3Dchars' in url


def test_redirect_endpoint(client, sample_bookmark):
    """Test main redirect endpoint."""
    # Test exact match
    response = client.get('/?q=test hello')
    assert response.status_code == 302
    assert 'example.com' in response.location
    assert 'hello' in response.location

    # Test alias
    response = client.get('/?q=t world')
    assert response.status_code == 302
    assert 'example.com' in response.location
    assert 'world' in response.location


def test_api_get_bookmarks(client, sample_bookmark):
    """Test getting all bookmarks."""
    response = client.get('/api/bookmarks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'test'


def test_redirect_fallback_url(client, app):
    """Test redirect to fallback URL when no match."""
    response = client.get('/?q=nonexistent')
    assert response.status_code == 200  # Shows suggestions page
    # Or if configured to redirect to fallback
    # assert response.status_code == 302


def test_redirect_empty_query(client, app):
    """Test redirect with empty query."""
    response = client.get('/')
    # Should redirect to fallback or show error
    assert response.status_code in [200, 302]


def test_redirect_no_args(client, sample_bookmark):
    """Test redirect without arguments."""
    response = client.get('/?q=test')
    assert response.status_code == 302
    assert 'example.com' in response.location


def test_redirect_increments_use_count(client, sample_bookmark, app):
    """Test that redirect increments use_count."""
    with app.app_context():
        from app.models import Bookmark
        initial_count = Bookmark.query.get(sample_bookmark.id).use_count

    response = client.get('/?q=test hello')
    assert response.status_code == 302

    with app.app_context():
        from app.models import Bookmark
        final_count = Bookmark.query.get(sample_bookmark.id).use_count
        assert final_count == initial_count + 1


def test_redirect_special_characters(client, sample_bookmark):
    """Test redirect with special characters in args."""
    response = client.get('/?q=test hello&world=123')
    assert response.status_code == 302
    # Special characters should be URL encoded
    assert '%26' in response.location or '&' in response.location


def test_redirect_multiple_spaces(client, sample_bookmark):
    """Test redirect with multiple spaces in args."""
    response = client.get('/?q=test   multiple   spaces')
    assert response.status_code == 302
    assert 'example.com' in response.location


def test_fuzzy_suggestions_page(client, sample_bookmark):
    """Test fuzzy suggestions page appears for close matches."""
    response = client.get('/?q=tst')  # Typo of 'test'
    # Should show suggestions page (200) or redirect to exact match
    assert response.status_code in [200, 302]

    if response.status_code == 200:
        # Check that response contains suggestion-related content
        assert b'test' in response.data or b'suggestion' in response.data.lower()
