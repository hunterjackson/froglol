from urllib.parse import quote_plus
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from app.models import Bookmark, Alias
from app import db


@dataclass
class RedirectResult:
    """Result of processing a redirect query."""

    url: Optional[str] = None
    suggestions: Optional[List[Dict]] = None


def parse_query(query: str) -> Tuple[str, str]:
    """
    Parse 'command arg1 arg2' into ('command', 'arg1 arg2').

    Args:
        query: The full query string from the browser

    Returns:
        Tuple of (command, args) where command is lowercase
    """
    parts = query.strip().split(maxsplit=1)
    command = parts[0].lower() if parts else ""
    args = parts[1] if len(parts) > 1 else ""
    return command, args


def substitute_args(url_template: str, args: str) -> str:
    """
    Replace %s in URL template with URL-encoded args.

    Args:
        url_template: URL template containing %s placeholder
        args: Arguments to substitute

    Returns:
        URL with args substituted and encoded
    """
    encoded_args = quote_plus(args) if args else ""
    return url_template.replace("%s", encoded_args)


def find_bookmark_by_name_or_alias(command: str) -> Optional[Bookmark]:
    """
    Find a bookmark by its name or any of its aliases.

    Args:
        command: The command to search for (case-insensitive)

    Returns:
        Bookmark object if found, None otherwise
    """
    from sqlalchemy import or_

    # Single query that checks both bookmarks and aliases
    bookmark = (
        Bookmark.query.outerjoin(Alias)
        .filter(or_(Bookmark.name == command, Alias.alias == command))
        .first()
    )

    return bookmark


def increment_usage(bookmark: Bookmark):
    """
    Increment the use_count for a bookmark.

    Args:
        bookmark: The bookmark to increment
    """
    bookmark.use_count += 1
    db.session.commit()


def process_redirect(query: str) -> RedirectResult:
    """
    Process a redirect query and return the result.

    Args:
        query: The full query string from the browser

    Returns:
        RedirectResult with either a URL to redirect to or None if no match found
    """
    if not query or not query.strip():
        # Empty query, return no match
        return RedirectResult(url=None)

    command, args = parse_query(query)

    # Try exact match
    bookmark = find_bookmark_by_name_or_alias(command)
    if bookmark:
        increment_usage(bookmark)
        final_url = substitute_args(bookmark.url, args)
        return RedirectResult(url=final_url)

    # No match found
    return RedirectResult(url=None)
