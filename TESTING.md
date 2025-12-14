# Testing Strategy

This document outlines the comprehensive testing strategy for Froglol, including how tests are organized, run, and enforced in CI/CD.

## Test Organization

The test suite is organized into distinct categories:

### 1. Unit Tests (`tests/test_units.py`) - 45 tests

Tests individual functions and components in isolation without external dependencies.

**Coverage:**
- `parse_query()` - Query string parsing (9 tests)
- `substitute_args()` - URL argument substitution (8 tests)
- `find_bookmark_by_name_or_alias()` - Database lookups (5 tests)
- `increment_usage()` - Usage tracking (3 tests)
- `process_redirect()` - Redirect orchestration (6 tests)
- `Bookmark` model - CRUD and validation (4 tests)
- `Alias` model - Relationships and constraints (5 tests)
- `FuzzyMatcher` class - Configuration and behavior (5 tests)

### 2. Integration Tests (`tests/test_integration.py`) - 26 tests

Tests complete workflows and end-to-end scenarios with all components working together.

**Coverage:**
- **End-to-End Redirect Flow** (8 tests)
  - Exact matches, aliases, fuzzy matching
  - Fallback behavior, special characters
  - Edge cases and error handling

- **Usage Tracking** (3 tests)
  - Increment verification
  - Alias tracking
  - Failed lookup behavior

- **CRUD Integration** (5 tests)
  - Create and immediately use bookmarks
  - Update URLs and verify redirect changes
  - Delete bookmarks and verify prevention
  - Add aliases after creation

- **Fuzzy Matching Integration** (3 tests)
  - Typo suggestions
  - Partial command matching
  - Multiple similar suggestions

- **Edge Cases** (5 tests)
  - Case insensitivity
  - Whitespace handling
  - Unicode support
  - Very long queries

- **Concurrent Usage** (2 tests)
  - Multiple redirects
  - Interleaved operations

### 3. API Tests (`tests/test_api.py`) - 20 tests

Tests REST API endpoints for bookmark management.

### 4. Service Tests (`tests/test_fuzzy_matcher.py`) - 12 tests

Tests fuzzy matching service functionality.

### 5. Redirect Tests (`tests/test_redirect.py`) - 11 tests

Tests redirect endpoint and helper functions.

## Total Test Count: 114 tests

## Running Tests Locally

### Run All Tests
```bash
# With coverage (recommended before pushing)
uv run pytest

# Fast run without coverage
uv run pytest --no-cov
```

### Run Specific Test Suites
```bash
# Unit tests only (fast)
uv run pytest tests/test_units.py -v

# Integration tests only
uv run pytest tests/test_integration.py -v

# API tests only
uv run pytest tests/test_api.py -v
```

### Run Specific Tests
```bash
# Run a specific test class
uv run pytest tests/test_integration.py::TestEndToEndRedirectFlow -v

# Run a specific test
uv run pytest tests/test_integration.py::TestEndToEndRedirectFlow::test_exact_bookmark_redirect -v

# Run tests matching a pattern
uv run pytest -k "redirect" -v
```

### Coverage Reports
```bash
# Terminal report with missing lines
uv run pytest --cov-report=term-missing

# HTML report (detailed)
uv run pytest
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## CI/CD Pipeline

### GitHub Actions Workflow

The test workflow (`.github/workflows/test.yml`) runs on every push and pull request:

```yaml
1. Run Unit Tests (45 tests)
   → pytest tests/test_units.py -v

2. Run Integration Tests (26 tests)
   → pytest tests/test_integration.py -v

3. Run All Tests with Coverage (114 tests)
   → pytest
   → Must reach 80% coverage or build fails
```

This approach provides:
- **Clear separation** in GitHub Actions UI
- **Fast failure** - unit tests fail first if broken
- **Explicit validation** - integration tests are clearly tracked
- **Complete coverage** - final step ensures all tests pass with coverage

### Test Matrix

Tests run on multiple Python versions:
- Python 3.10
- Python 3.11
- Python 3.12

All versions must pass for the build to succeed.

### Branch Protection

When branch protection is enabled (see `.github/BRANCH_PROTECTION.md`), merges are blocked if:

- ❌ Any unit test fails
- ❌ Any integration test fails
- ❌ Coverage is below 80%
- ❌ Linting fails
- ❌ Security checks fail

## Coverage Requirements

- **Minimum**: 80% code coverage
- **Current**: ~89% coverage
- **Scope**: `app/` directory only (excludes tests, config)

### Viewing Coverage in CI

1. Go to GitHub Actions run
2. Click on "test" job for Python 3.11
3. Expand "Run all tests with coverage" step
4. View coverage report at the bottom
5. Download "coverage-report" artifact for HTML report

## Test Development Guidelines

### Writing Unit Tests

Unit tests should:
- Test one function/method at a time
- Use mocks for external dependencies
- Be fast (< 100ms each)
- Have clear, descriptive names
- Test edge cases and error conditions

Example:
```python
def test_parse_query_with_empty_string():
    """Test parsing empty query returns empty command and args."""
    command, args = parse_query("")
    assert command == ""
    assert args == ""
```

### Writing Integration Tests

Integration tests should:
- Test complete user workflows
- Use real database (in-memory for tests)
- Verify multiple components work together
- Test realistic scenarios
- Be organized into test classes by feature

Example:
```python
class TestEndToEndRedirectFlow:
    def test_exact_bookmark_redirect(self, seeded_client):
        """Test redirecting to an exact bookmark match."""
        response = seeded_client.get("/?q=google python tutorial")
        assert response.status_code == 302
        assert "google.com/search" in response.location
        assert "python+tutorial" in response.location
```

### Test Fixtures

Common fixtures (in `tests/conftest.py`):
- `app` - Flask app instance with test config
- `client` - Test client for making requests
- `sample_bookmark` - Pre-created bookmark for testing
- `seeded_app` - App with realistic bookmark data
- `seeded_client` - Client with seeded data

## Debugging Failed Tests

### Locally
```bash
# Run with verbose output
uv run pytest -v

# Run with extra debugging
uv run pytest -vv

# Run with print statements visible
uv run pytest -s

# Run last failed tests only
uv run pytest --lf

# Stop at first failure
uv run pytest -x
```

### In CI
1. Click on failed test in GitHub Actions
2. View full test output
3. Check "Run all tests with coverage" step
4. Download artifacts if needed

## Test Performance

Current test run times (approximate):
- Unit tests: ~0.5s
- Integration tests: ~0.8s
- Full suite with coverage: ~1.7s

Target: Keep full suite under 5 seconds.

## Continuous Improvement

When adding new features:
1. Write unit tests first (TDD approach)
2. Add integration tests for workflows
3. Run tests locally before pushing
4. Verify CI passes before requesting review
5. Maintain or improve coverage percentage

## Questions?

- See `.github/BRANCH_PROTECTION.md` for CI/CD setup
- Check pytest logs for detailed error messages
- Review test fixtures in `tests/conftest.py`
- Ask in pull request comments
