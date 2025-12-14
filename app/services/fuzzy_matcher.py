from typing import List, Dict
import time
from rapidfuzz import fuzz
from sqlalchemy.orm import joinedload
from app.models import Bookmark
from app import db


class FuzzyMatcher:
    def __init__(self, threshold: int = 60, limit: int = 3, cache_ttl: int = 60):
        """
        Initialize fuzzy matcher.

        Args:
            threshold: Minimum similarity score (0-100) to consider a match
            limit: Maximum number of suggestions to return
            cache_ttl: Cache time-to-live in seconds (default: 60)
        """
        self.threshold = threshold
        self.limit = limit
        self.cache_ttl = cache_ttl
        self._commands_cache = None
        self._cache_timestamp = None

    def _get_all_commands(self) -> Dict[str, Bookmark]:
        """
        Get all available commands (bookmark names and aliases) with caching.

        Returns:
            Dictionary mapping command name to Bookmark object
        """
        now = time.time()

        # Return cached data if still valid
        if (
            self._commands_cache is not None
            and self._cache_timestamp is not None
            and now - self._cache_timestamp < self.cache_ttl
        ):
            return self._commands_cache

        # Rebuild cache with eager loading to avoid N+1 queries
        commands = {}
        bookmarks = Bookmark.query.options(joinedload(Bookmark.aliases)).all()

        for bookmark in bookmarks:
            # Add bookmark name
            commands[bookmark.name] = bookmark

            # Add all aliases
            for alias in bookmark.aliases:
                commands[alias.alias] = bookmark

        # Update cache
        self._commands_cache = commands
        self._cache_timestamp = now

        return commands

    def find_similar_commands(self, query: str) -> List[Dict]:
        """
        Find similar commands using fuzzy matching.

        Args:
            query: The command to find matches for

        Returns:
            List of up to 'limit' suggestions, each containing:
            - name: The command name
            - url: The bookmark URL
            - score: Similarity score
            - use_count: Usage count for this bookmark
        """
        commands = self._get_all_commands()

        if not commands:
            return []

        # Calculate similarity scores
        matches = []
        for command_name, bookmark in commands.items():
            score = fuzz.ratio(query.lower(), command_name.lower())

            if score >= self.threshold:
                matches.append(
                    {
                        "name": command_name,
                        "url": bookmark.url,
                        "description": bookmark.description,
                        "score": score,
                        "use_count": bookmark.use_count,
                        "bookmark_id": bookmark.id,
                    }
                )

        # Sort by score (descending), then by use_count (descending)
        matches.sort(key=lambda x: (x["score"], x["use_count"]), reverse=True)

        # Return top matches (deduplicated by bookmark_id)
        seen_bookmarks = set()
        unique_matches = []

        for match in matches:
            if match["bookmark_id"] not in seen_bookmarks:
                seen_bookmarks.add(match["bookmark_id"])
                unique_matches.append(match)

                if len(unique_matches) >= self.limit:
                    break

        return unique_matches
