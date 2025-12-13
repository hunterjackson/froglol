from app import db
from app.models import Bookmark, Alias


SEED_BOOKMARKS = [
    {
        'name': 'froglol',
        'url': 'http://localhost:5000/manage',
        'description': 'Froglol bookmark management',
        'aliases': ['manage', 'list']
    },
    {
        'name': 'google',
        'url': 'https://www.google.com/search?q=%s',
        'description': 'Google search',
        'aliases': ['g']
    },
    {
        'name': 'github',
        'url': 'https://github.com/search?q=%s',
        'description': 'GitHub search',
        'aliases': ['gh']
    },
    {
        'name': 'youtube',
        'url': 'https://www.youtube.com/results?search_query=%s',
        'description': 'YouTube search',
        'aliases': ['yt']
    },
    {
        'name': 'wikipedia',
        'url': 'https://en.wikipedia.org/wiki/Special:Search?search=%s',
        'description': 'Wikipedia search',
        'aliases': ['wiki', 'w']
    },
    {
        'name': 'stackoverflow',
        'url': 'https://stackoverflow.com/search?q=%s',
        'description': 'Stack Overflow search',
        'aliases': ['so', 'stack']
    },
    {
        'name': 'reddit',
        'url': 'https://www.reddit.com/search?q=%s',
        'description': 'Reddit search',
        'aliases': ['r']
    },
    {
        'name': 'twitter',
        'url': 'https://twitter.com/search?q=%s',
        'description': 'Twitter search',
        'aliases': ['tw']
    },
    {
        'name': 'amazon',
        'url': 'https://www.amazon.com/s?k=%s',
        'description': 'Amazon product search',
        'aliases': ['amz']
    },
    {
        'name': 'chatgpt',
        'url': 'https://chat.openai.com/',
        'description': 'ChatGPT by OpenAI',
        'aliases': ['gpt', 'openai']
    },
    {
        'name': 'claude',
        'url': 'https://claude.ai/',
        'description': 'Claude by Anthropic',
        'aliases': ['anthropic']
    },
    {
        'name': 'gemini',
        'url': 'https://gemini.google.com/',
        'description': 'Gemini by Google',
        'aliases': ['bard']
    },
]


def seed_initial_data():
    """Populate database with initial bookmarks."""
    # Add seed bookmarks
    for bookmark_data in SEED_BOOKMARKS:
        bookmark = Bookmark(
            name=bookmark_data['name'],
            url=bookmark_data['url'],
            description=bookmark_data['description']
        )
        db.session.add(bookmark)
        db.session.flush()  # Get the bookmark ID

        # Add aliases
        for alias_name in bookmark_data.get('aliases', []):
            alias = Alias(alias=alias_name, bookmark_id=bookmark.id)
            db.session.add(alias)

    db.session.commit()
