# Branch Protection and CI/CD Setup Guide

This guide explains how to set up branch protection rules to ensure all code changes pass tests before being merged.

## Overview

The repository includes automated testing and quality checks via GitHub Actions:

- **Tests**: Run on Python 3.10, 3.11, and 3.12
- **Code Coverage**: Enforces minimum 80% test coverage
- **Linting**: Runs Ruff for code style and quality
- **Security Checks**: Scans for vulnerabilities using Safety and Bandit
- **Docker Builds**: Automatically builds and publishes images

## Setting Up Branch Protection

### Step 1: Enable Branch Protection Rules

1. Go to your GitHub repository
2. Click **Settings** → **Branches**
3. Click **Add branch protection rule**
4. Enter branch name pattern: `master` (or `main`)

### Step 2: Configure Protection Rules

Enable the following settings:

#### Required Status Checks

✅ **Require status checks to pass before merging**
   - Check: **Require branches to be up to date before merging**

   Select these required checks:
   - `test (3.10)` - Tests on Python 3.10
   - `test (3.11)` - Tests on Python 3.11
   - `test (3.12)` - Tests on Python 3.12
   - `lint` - Code linting with Ruff
   - `security` - Security vulnerability scans
   - `build-and-push` - Docker image build (optional but recommended)

#### Pull Request Requirements

✅ **Require a pull request before merging**
   - **Require approvals**: Set to 1 (recommended for team projects)
   - ✅ **Dismiss stale pull request approvals when new commits are pushed**
   - ✅ **Require review from Code Owners** (if you have CODEOWNERS file)

#### Additional Protections

✅ **Require conversation resolution before merging**
✅ **Require linear history** (prevents merge commits, cleaner history)
✅ **Include administrators** (enforce rules on admins too)

### Step 3: Save Rules

Click **Create** or **Save changes**

## What Gets Blocked

With these rules enabled, the following will be **blocked** from merging:

- ❌ Code that fails any test
- ❌ Code with < 80% test coverage
- ❌ Code with linting errors
- ❌ Code with security vulnerabilities (high severity)
- ❌ Pull requests without required approvals
- ❌ Branches that are out of date with master

## Workflow Details

### Test Workflow (`.github/workflows/test.yml`)

Runs on every push and pull request:

1. **Tests** - Runs pytest across Python 3.10, 3.11, 3.12
   - Must pass all tests
   - Must meet 80% code coverage threshold
   - Uploads coverage to Codecov (optional)

2. **Lint** - Code quality checks
   - Ruff linting for PEP 8 compliance
   - Ruff formatting check

3. **Security** - Vulnerability scanning
   - Safety: Checks for known vulnerabilities in dependencies
   - Bandit: Checks for common security issues in code

### Docker Build Workflow (`.github/workflows/docker-build.yml`)

Runs on pushes to master/main:

1. Builds Docker image
2. Pushes to GitHub Container Registry
3. Tags with appropriate version labels

## Running Tests Locally

Before pushing, run tests locally to catch issues early:

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_api.py -v

# Run tests without coverage (faster)
pytest --no-cov

# Run linting
pip install ruff
ruff check app/ tests/
ruff format --check app/ tests/

# Run security checks
pip install safety bandit
safety check
bandit -r app/
```

## Coverage Requirements

The project enforces **80% minimum code coverage**. To check coverage:

```bash
# Run tests with coverage report
pytest

# View detailed HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Coverage is calculated for the `app/` directory only, excluding:
- Test files
- Configuration files
- Migration scripts

## Bypassing Protections (Emergency Only)

If you're an admin and need to bypass protections in an emergency:

1. Temporarily disable branch protection:
   - Settings → Branches → Edit rule → Uncheck protections
   - Make your changes
   - **Re-enable protections immediately**

2. Use admin override:
   - Uncheck "Include administrators" in branch protection
   - Make changes as admin
   - **Re-check immediately after**

⚠️ **Warning**: Only use in true emergencies. Every bypass should be documented.

## Best Practices

### For Contributors

1. **Write tests first** - Add tests for new features
2. **Run tests locally** - Catch issues before pushing
3. **Keep PRs small** - Easier to review and test
4. **Update tests** - When changing existing code
5. **Check coverage** - Ensure new code is tested

### For Reviewers

1. **Check test coverage** - Ensure new code is well-tested
2. **Run tests locally** - Verify tests actually test the feature
3. **Review test quality** - Not just quantity
4. **Verify CI passes** - Don't merge until all checks are green

## Troubleshooting

### Tests Pass Locally But Fail in CI

**Possible causes:**
- Environment differences (check Python version)
- Missing dependencies in requirements.txt
- Database state issues
- Timezone or locale differences

**Solution:**
```bash
# Test with same Python version as CI
python3.11 -m pytest

# Clean test environment
rm -rf .pytest_cache htmlcov .coverage
pytest
```

### Coverage Threshold Not Met

**Solution:**
```bash
# Find uncovered code
pytest --cov-report=term-missing

# Add tests for missing coverage
# Then verify:
pytest --cov-report=html
open htmlcov/index.html
```

### Linting Failures

**Solution:**
```bash
# Auto-fix most issues
ruff check --fix app/ tests/
ruff format app/ tests/

# Check what remains
ruff check app/ tests/
```

### Branch Out of Date

**Solution:**
```bash
# Update your branch
git checkout your-branch
git fetch origin
git rebase origin/master  # or merge if preferred
git push --force-with-lease
```

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## Questions?

- Check GitHub Actions logs for detailed error messages
- Review test output for specific failures
- Ask in pull request comments for help
