import pytest
from app.models import Bookmark, Alias
from app import db


def test_get_bookmarks(client, sample_bookmark):
    """Test getting all bookmarks."""
    response = client.get('/api/bookmarks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'test'


def test_get_bookmark_by_id(client, sample_bookmark):
    """Test getting a specific bookmark."""
    response = client.get(f'/api/bookmarks/{sample_bookmark.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'test'
    assert data['url'] == 'https://example.com/search?q=%s'


def test_get_bookmark_not_found(client):
    """Test getting a non-existent bookmark."""
    response = client.get('/api/bookmarks/999')
    assert response.status_code == 404


def test_create_bookmark(client):
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


def test_create_bookmark_with_aliases(client):
    """Test creating a bookmark with aliases."""
    response = client.post('/api/bookmarks', json={
        'name': 'google',
        'url': 'https://google.com/search?q=%s',
        'description': 'Google search',
        'aliases': ['g', 'search']
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'google'
    assert len(data['aliases']) == 2
    assert any(a['alias'] == 'g' for a in data['aliases'])


def test_create_bookmark_missing_fields(client):
    """Test creating a bookmark without required fields."""
    # Missing name
    response = client.post('/api/bookmarks', json={
        'url': 'https://example.com'
    })
    assert response.status_code == 400

    # Missing URL
    response = client.post('/api/bookmarks', json={
        'name': 'test'
    })
    assert response.status_code == 400

    # Empty request
    response = client.post('/api/bookmarks', json={})
    assert response.status_code == 400


def test_create_bookmark_duplicate_name(client, sample_bookmark):
    """Test creating a bookmark with a duplicate name."""
    response = client.post('/api/bookmarks', json={
        'name': 'test',
        'url': 'https://example.com'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'already exists' in data['error'].lower()


def test_update_bookmark(client, sample_bookmark):
    """Test updating a bookmark."""
    response = client.put(f'/api/bookmarks/{sample_bookmark.id}', json={
        'name': 'updated',
        'url': 'https://updated.com',
        'description': 'Updated description'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'updated'
    assert data['url'] == 'https://updated.com'
    assert data['description'] == 'Updated description'


def test_update_bookmark_partial(client, sample_bookmark):
    """Test partially updating a bookmark."""
    response = client.put(f'/api/bookmarks/{sample_bookmark.id}', json={
        'description': 'New description only'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'test'  # Unchanged
    assert data['description'] == 'New description only'


def test_update_bookmark_duplicate_name(client, sample_bookmark, app):
    """Test updating a bookmark to a duplicate name."""
    with app.app_context():
        # Create another bookmark
        other = Bookmark(name='other', url='https://other.com')
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    response = client.put(f'/api/bookmarks/{other_id}', json={
        'name': 'test'  # Conflicts with sample_bookmark
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'already exists' in data['error'].lower()


def test_update_bookmark_not_found(client):
    """Test updating a non-existent bookmark."""
    response = client.put('/api/bookmarks/999', json={'name': 'test'})
    assert response.status_code == 404


def test_delete_bookmark(client, sample_bookmark):
    """Test deleting a bookmark."""
    bookmark_id = sample_bookmark.id
    response = client.delete(f'/api/bookmarks/{bookmark_id}')
    assert response.status_code == 204

    # Verify it's deleted
    response = client.get(f'/api/bookmarks/{bookmark_id}')
    assert response.status_code == 404


def test_delete_bookmark_not_found(client):
    """Test deleting a non-existent bookmark."""
    response = client.delete('/api/bookmarks/999')
    assert response.status_code == 404


def test_add_alias(client, sample_bookmark):
    """Test adding an alias to a bookmark."""
    response = client.post(f'/api/bookmarks/{sample_bookmark.id}/aliases', json={
        'alias': 'newtest'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['alias'] == 'newtest'


def test_add_alias_missing_field(client, sample_bookmark):
    """Test adding an alias without required field."""
    response = client.post(f'/api/bookmarks/{sample_bookmark.id}/aliases', json={})
    assert response.status_code == 400


def test_add_alias_duplicate(client, sample_bookmark):
    """Test adding a duplicate alias."""
    response = client.post(f'/api/bookmarks/{sample_bookmark.id}/aliases', json={
        'alias': 't'  # Already exists from sample_bookmark
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'already exists' in data['error'].lower()


def test_add_alias_conflicts_with_bookmark_name(client, sample_bookmark):
    """Test adding an alias that conflicts with a bookmark name."""
    response = client.post(f'/api/bookmarks/{sample_bookmark.id}/aliases', json={
        'alias': 'test'  # Conflicts with bookmark name
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'conflicts' in data['error'].lower()


def test_delete_alias(client, sample_bookmark, app):
    """Test deleting an alias."""
    with app.app_context():
        alias = Alias.query.filter_by(alias='t').first()
        alias_id = alias.id

    response = client.delete(f'/api/aliases/{alias_id}')
    assert response.status_code == 204

    # Verify it's deleted
    response = client.delete(f'/api/aliases/{alias_id}')
    assert response.status_code == 404


def test_delete_alias_not_found(client):
    """Test deleting a non-existent alias."""
    response = client.delete('/api/aliases/999')
    assert response.status_code == 404


def test_cascade_delete_aliases(client, sample_bookmark, app):
    """Test that deleting a bookmark cascades to its aliases."""
    with app.app_context():
        # Verify alias exists
        alias = Alias.query.filter_by(alias='t').first()
        assert alias is not None
        alias_id = alias.id

    # Delete the bookmark
    response = client.delete(f'/api/bookmarks/{sample_bookmark.id}')
    assert response.status_code == 204

    # Verify alias is also deleted
    with app.app_context():
        alias = Alias.query.get(alias_id)
        assert alias is None
