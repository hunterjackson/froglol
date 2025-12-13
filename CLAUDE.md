# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Froglol is a URL bookmark redirection server inspired by Facebook's bunnylol. It allows users to create custom shortcuts for websites and use them directly from the browser's URL bar (e.g., `google python tutorials` redirects to Google search).

**Key Features:**
- Fast URL redirection via browser search engine integration
- Dynamic search with `%s` placeholder in URLs
- Command aliases (multiple shortcuts for same bookmark)
- Fuzzy matching with suggestions when commands are mistyped
- Usage tracking for bookmarks
- Auto-seeding with common bookmarks on first run

## Development Commands

### Local Development (using uv)

```bash
# Setup
uv venv
uv pip install -r requirements.txt

# Run development server
uv run python run.py

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_redirect.py::test_name -v

# Reset database (deletes and re-seeds)
rm -f instance/froglol.db
uv run python run.py  # Auto-seeds on first run
```

### Docker Development

```bash
# Start application
make up
# OR: docker compose up -d

# View logs
make logs
# OR: docker compose logs -f

# Run tests in container
make test
# OR: docker compose run --rm froglol pytest -v

# Access container shell
make shell
# OR: docker compose exec froglol /bin/sh

# Stop and clean everything
make clean
# OR: docker compose down -v && rm -rf instance/froglol.db

# Rebuild after code changes
docker compose up -d --build
```

## Architecture

### Application Structure

The app uses the **Flask application factory pattern** with blueprints for modularity:

- **`app/__init__.py`**: Application factory (`create_app()`) that initializes Flask, SQLAlchemy, registers blueprints, and auto-seeds database on first run
- **`app/models.py`**: SQLAlchemy models (`Bookmark` and `Alias`) with relationship handling
- **`app/routes/`**: Blueprint modules for different concerns:
  - `redirect.py`: Main redirect endpoint (`/`) that handles browser queries
  - `bookmarks.py`: REST API for CRUD operations on bookmarks/aliases
  - `ui.py`: Web UI routes for managing bookmarks
- **`app/services/`**: Business logic separated from routes:
  - `redirect_service.py`: Core redirect logic (query parsing, bookmark lookup, URL substitution)
  - `fuzzy_matcher.py`: Fuzzy matching using rapidfuzz with configurable threshold/limit

### Request Flow

1. Browser sends query to `/?q=command args`
2. `redirect.py` route extracts query parameter
3. `redirect_service.process_redirect()` orchestrates:
   - Parse query into command + args
   - Exact match lookup (bookmark name or alias)
   - If found: increment usage, substitute `%s` in URL, redirect
   - If not found: fuzzy match for suggestions
   - If no suggestions: fallback to configured default URL
4. Return either redirect (302) or suggestions page

### Database Models

**Bookmark** (primary entity):
- `name`: Unique command name (indexed)
- `url`: URL template with optional `%s` placeholder
- `description`: Optional description
- `use_count`: Tracks usage frequency
- `aliases`: One-to-many relationship to Alias

**Alias** (alternate names for bookmarks):
- `alias`: Unique alternate command (indexed)
- `bookmark_id`: Foreign key to Bookmark
- Cascade delete when parent bookmark deleted

### Configuration

All configuration lives in `config.py` as `Config` class, loaded from environment variables:
- `SECRET_KEY`: Flask session key (use strong value in production)
- `DATABASE_URL`: Database URI (defaults to SQLite in `instance/froglol.db`)
- `DEFAULT_FALLBACK_URL`: Fallback when no match (defaults to Google search)
- `FUZZY_MATCH_THRESHOLD`: Min similarity score 0-100 (default: 60)
- `FUZZY_MATCH_LIMIT`: Max suggestions to show (default: 3)

Use `.env` file for local overrides (see `.env.example`).

### Database Initialization

The app automatically creates tables and seeds initial data on first run:
- Detection happens in `create_app()` by checking if SQLite file exists
- Seeding logic is in `app/seed.py` (called via `seed_initial_data()`)
- Seeds ~12 bookmarks including: manage page, search engines (Google, GitHub, YouTube, etc.), AI chatbots (ChatGPT, Claude, Gemini)

## Testing

Tests use pytest with Flask testing utilities:
- Test configuration in `pytest.ini`
- Test fixtures in `tests/conftest.py` (provides `app` and `client` fixtures)
- Tests in `tests/test_redirect.py`

When writing tests:
- Use the `client` fixture for making requests
- Use the `app` fixture for app context operations
- Tests run with isolated in-memory database
- Fixtures are session/function scoped as appropriate

## Docker Deployment

Production deployment uses:
- **Base image**: Python 3.11 slim
- **WSGI server**: Gunicorn (2 workers by default, configured in `gunicorn.conf.py`)
- **Resource limits**: 0.5 CPU, 256MB RAM (suitable for small user base)
- **Security**: Non-root user (UID 1000), read-only filesystem, no new privileges
- **Health checks**: Every 30s on `/` endpoint
- **Persistence**: `./instance` directory mounted as volume for SQLite database

See `DOCKER.md` for detailed deployment and scaling information.

## Important Patterns

### URL Substitution
The `%s` placeholder in URLs is replaced with URL-encoded arguments:
- `https://google.com/search?q=%s` + args "python" → `https://google.com/search?q=python`
- Empty args: `%s` is replaced with empty string
- Encoding uses `urllib.parse.quote_plus`

### Fuzzy Matching
Uses `rapidfuzz.fuzz.ratio()` for similarity scoring:
- Returns matches above threshold, sorted by score then use_count
- Deduplicates by bookmark_id (since aliases point to same bookmark)
- Limited to configured max suggestions

### Alias Handling
Aliases are first-class alternate commands:
- Lookup checks both `Bookmark.name` and `Alias.alias`
- Both are indexed for performance
- Cascade delete when bookmark is removed

## Common Pitfalls

- **Database location**: SQLite file is in `instance/froglol.db`, not at repo root
- **First run detection**: Only works for SQLite; other databases won't auto-seed
- **Case sensitivity**: Commands are normalized to lowercase during lookup
- **URL encoding**: Always use `quote_plus` for args to handle special characters
- **Fuzzy match deduplication**: Must deduplicate by `bookmark_id` to avoid showing same bookmark multiple times via different aliases
