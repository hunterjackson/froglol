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


def test_api_create_bookmark(client):
    """Test creating a new bookmark."""
    response = client.post('/api/bookmarks', json={
        'name': 'github',
        'url': 'https://github.com/search?q=%s',
        'description': 'GitHub search'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'github'
    assert data['url'] == 'https://github.com/search?q=%s'
