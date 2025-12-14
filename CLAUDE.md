# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

- **Testing Guide**: See `TESTING.md` for comprehensive testing documentation
- **Branch Protection**: See `.github/BRANCH_PROTECTION.md` for CI/CD and merge requirements
- **Docker Guide**: See `DOCKER.md` for deployment information

**⚠️ Important:** Always use `uv run` for Python commands, never direct `python` or `pytest`.

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

### Important: Always Use `uv`

This project uses **`uv`** for dependency management and command execution. Always prefix commands with `uv run`:

- ✅ **Correct**: `uv run pytest`
- ❌ **Wrong**: `pytest` or `python -m pytest`
- ✅ **Correct**: `uv run python run.py`
- ❌ **Wrong**: `python run.py`

Using `uv run` ensures the correct virtual environment and dependencies are used.

### Local Development (using uv)

```bash
# Setup
uv venv
uv pip install -r requirements.txt

# Run development server
uv run python run.py

# Run all tests
uv run pytest

# Run specific test suites
uv run pytest tests/test_units.py -v          # Unit tests only
uv run pytest tests/test_integration.py -v    # Integration tests only
uv run pytest tests/test_api.py -v            # API tests only

# Run specific test
uv run pytest tests/test_redirect.py::test_name -v

# Run tests without coverage (faster for development)
uv run pytest --no-cov

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

The project has comprehensive test coverage (114 tests, 89% coverage) organized into:

### Test Organization

- **`tests/test_units.py`** (45 tests) - Unit tests for individual functions and components
  - Tests in isolation without external dependencies
  - Fast execution, focused on single responsibilities
  - Examples: `parse_query()`, `substitute_args()`, model CRUD operations

- **`tests/test_integration.py`** (26 tests) - Integration tests for complete workflows
  - End-to-end redirect flows (exact match, alias, fuzzy, fallback)
  - CRUD integration (create and immediately use bookmarks)
  - Usage tracking verification
  - Edge cases (Unicode, special characters, concurrent operations)

- **`tests/test_api.py`** (20 tests) - REST API endpoint tests
- **`tests/test_fuzzy_matcher.py`** (12 tests) - Fuzzy matching service tests
- **`tests/test_redirect.py`** (11 tests) - Redirect endpoint and helper tests

### Test Configuration

- **Config**: `pytest.ini` sets test paths, coverage requirements (80% minimum)
- **Fixtures**: `tests/conftest.py` provides:
  - `app` - Flask app instance with test config
  - `client` - Test client for making HTTP requests
  - `sample_bookmark` - Pre-created bookmark for testing
  - `seeded_app` / `seeded_client` - App with realistic seed data
- **Database**: Tests use isolated in-memory SQLite database
- **Coverage**: Enforced at 80% minimum, currently at 89%

### When Writing Tests

**For Unit Tests:**
- Test one function/method at a time
- Mock external dependencies
- Use descriptive names: `test_parse_query_with_empty_string()`
- Test edge cases and error conditions
- Keep tests fast (< 100ms each)

**For Integration Tests:**
- Test complete user workflows
- Use real database (in-memory)
- Organize into test classes by feature
- Verify multiple components work together
- Example: Create bookmark via API, then redirect using it

**General Guidelines:**
- Always use `uv run pytest` to run tests
- Use the `client` fixture for making HTTP requests
- Use the `app` fixture for app context operations
- Write tests before writing code (TDD approach recommended)
- Run tests locally before pushing: `uv run pytest`
- Check coverage: `uv run pytest --cov-report=html`

### CI/CD Integration

All tests run automatically in GitHub Actions on every push/PR:
1. Unit tests run first (fast failure)
2. Integration tests run second (workflow validation)
3. Full suite with coverage (must reach 80%)

Branch protection blocks merges if:
- Any test fails
- Coverage drops below 80%
- Linting fails

See `TESTING.md` for detailed testing guide and `.github/BRANCH_PROTECTION.md` for CI/CD setup.

### When to Add Tests

**Adding a new function/method:**
1. Write unit test in `tests/test_units.py` first (TDD)
2. Implement the function
3. Verify test passes: `uv run pytest tests/test_units.py -k test_your_function`

**Adding a new API endpoint:**
1. Add unit tests for any new service functions
2. Add API tests in `tests/test_api.py` for endpoint behavior
3. Add integration test in `tests/test_integration.py` for complete workflow

**Adding a new user workflow:**
1. Add integration test in `tests/test_integration.py` showing the complete flow
2. Add unit tests for any new helper functions
3. Run integration tests: `uv run pytest tests/test_integration.py -v`

**Fixing a bug:**
1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify the test now passes
4. This prevents regression

**Modifying existing code:**
1. Run existing tests first: `uv run pytest`
2. Update tests if behavior changed intentionally
3. Add new tests for new edge cases
4. Ensure coverage doesn't drop

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

### Development Environment
- **Using `uv`**: ALWAYS use `uv run` prefix for Python commands. Direct `python` or `pytest` may use wrong environment or dependencies
- **Virtual environment**: Created with `uv venv`, not standard `python -m venv`
- **Installing packages**: Use `uv pip install`, not `pip install`

### Database
- **Database location**: SQLite file is in `instance/froglol.db`, not at repo root
- **First run detection**: Only works for SQLite; other databases won't auto-seed
- **Case sensitivity**: Commands are normalized to lowercase during lookup

### URL Handling
- **URL encoding**: Always use `quote_plus` for args to handle special characters
- **Placeholder position**: `%s` can appear anywhere in URL, gets replaced with encoded args

### Testing
- **Test isolation**: Each test uses fresh in-memory database, no state carries over
- **Fixtures**: Use `seeded_app`/`seeded_client` for tests needing realistic data, not `sample_bookmark`
- **Coverage**: Don't commit code that drops coverage below 80%
- **Fuzzy match deduplication**: Must deduplicate by `bookmark_id` to avoid showing same bookmark multiple times via different aliases
- **Running tests**: Always use `uv run pytest`, never `pytest` directly

### Code Changes
- **Write tests first**: Add tests before implementing features (TDD)
- **Run tests before committing**: Use `uv run pytest` to catch issues early
- **Integration tests**: Add integration tests for any user-facing workflow changes
- **Breaking changes**: Update both unit tests and integration tests when changing behavior
