from typing import List, Dict
from rapidfuzz import fuzz
from app.models import Bookmark


class FuzzyMatcher:
    def __init__(self, threshold: int = 60, limit: int = 3):
        """
        Initialize fuzzy matcher.

        Args:
            threshold: Minimum similarity score (0-100) to consider a match
            limit: Maximum number of suggestions to return
        """
        self.threshold = threshold
        self.limit = limit
        self._cache = None

    def _get_all_commands(self) -> Dict[str, Bookmark]:
        """
        Get all available commands (bookmark names and aliases).

        Returns:
            Dictionary mapping command name to Bookmark object
        """
        commands = {}

        # Get all bookmarks
        bookmarks = Bookmark.query.all()

        for bookmark in bookmarks:
            # Add bookmark name
            commands[bookmark.name] = bookmark

            # Add all aliases
            for alias in bookmark.aliases:
                commands[alias.alias] = bookmark

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
