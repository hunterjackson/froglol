# Git Hooks

This directory contains git hooks that automatically run during git operations.

## Setup

To enable these hooks, run:

```bash
git config core.hooksPath .githooks
```

This is a **one-time setup per clone**. Each developer needs to run this command after cloning the repository.

## Available Hooks

### pre-commit

Automatically runs before every commit to ensure code quality.

**What it does:**
1. Finds all staged Python files
2. Runs `ruff check --fix` to auto-fix linting issues
3. Runs `ruff format` to format code
4. Re-stages files that were modified
5. **Verifies** all linting issues are resolved (runs `ruff check app/ tests/`)
6. **Verifies** formatting is correct (runs `ruff format --check app/ tests/`)
7. Blocks commit if any issues remain

**Why the verification steps?**

Steps 5 and 6 run the **exact same commands** that GitHub Actions will run. This ensures that if your commit passes the hook, it will **guaranteed pass** the GitHub Actions lint check. This makes it impossible for linting failures to reach GitHub.

**Example output:**
```
Running ruff checks and formatting...
Checking and fixing Python files:
app/models.py
app/routes/bookmarks.py

1. Running ruff check --fix...
✓ Fixed 3 issues

2. Running ruff format...
✓ Formatted 2 files

3. Re-staging files modified by ruff...
   ✓ app/models.py
   ✓ app/routes/bookmarks.py

4. Verifying all linting issues are resolved...
✓ All checks passed

5. Verifying formatting is correct...
✓ 17 files already formatted

✅ All checks passed! Your code will pass GitHub Actions lint checks.
```

**If the hook blocks your commit:**
- Fix the issues manually that ruff couldn't auto-fix
- Run `uv run ruff check app/ tests/` to see what needs fixing
- Once fixed, try committing again

## Bypassing Hooks (Emergency Only)

If you absolutely need to bypass the hooks:

```bash
git commit --no-verify -m "Your message"
```

⚠️ **Warning:** Only use `--no-verify` in emergencies. All code should pass ruff checks before committing.

## Testing Hooks

To test the pre-commit hook without committing:

```bash
# Make some changes to Python files
git add .

# Test the hook manually
.githooks/pre-commit
```

## Requirements

- **uv**: Python package manager (hooks use `uv run ruff`)
- **ruff**: Linter and formatter (installed via requirements.txt)

If you don't have uv installed, see the main README for setup instructions.

## Troubleshooting

**"Permission denied" error:**
```bash
chmod +x .githooks/pre-commit
```

**Hook not running:**
```bash
# Check if hooks path is configured
git config --get core.hooksPath

# If empty, run setup command
git config core.hooksPath .githooks
```

**Ruff not found:**
```bash
# Install dependencies
uv pip install -r requirements.txt
```
