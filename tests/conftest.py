import pytest
from app import create_app, db
from app.models import Bookmark, Alias


@pytest.fixture
def app():
    """Create and configure a test app instance."""

    # Create test config class to prevent auto-seeding
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SECRET_KEY = "test-secret-key"
        DEFAULT_FALLBACK_URL = "https://www.google.com/search?q=%s"
        FUZZY_MATCH_THRESHOLD = 60
        FUZZY_MATCH_LIMIT = 3

    app = create_app(config_class=TestConfig)

    with app.app_context():
        db.create_all()
        # Don't auto-seed in tests - let each test control its data
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def sample_bookmark(app):
    """Create a sample bookmark for testing."""
    with app.app_context():
        bookmark = Bookmark(
            name="test",
            url="https://example.com/search?q=%s",
            description="Test bookmark",
        )
        db.session.add(bookmark)
        db.session.commit()

        alias = Alias(alias="t", bookmark_id=bookmark.id)
        db.session.add(alias)
        db.session.commit()

        # Eagerly load the ID before exiting context
        bookmark_id = bookmark.id

    # Return a simple object with the ID
    class BookmarkInfo:
        def __init__(self, id):
            self.id = id

    return BookmarkInfo(bookmark_id)
