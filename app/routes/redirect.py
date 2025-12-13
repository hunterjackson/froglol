from flask import Blueprint, request, redirect, render_template, current_app
from app.services.redirect_service import process_redirect
from app.services.fuzzy_matcher import FuzzyMatcher

bp = Blueprint('redirect', __name__)


@bp.route('/')
def index():
    """
    Main redirect endpoint.
    Receives query from browser search bar and redirects to appropriate URL.
    """
    query = request.args.get('q', '')

    # Initialize fuzzy matcher with config settings
    fuzzy_matcher = FuzzyMatcher(
        threshold=current_app.config['FUZZY_MATCH_THRESHOLD'],
        limit=current_app.config['FUZZY_MATCH_LIMIT']
    )

    # Process the redirect
    result = process_redirect(
        query,
        fuzzy_matcher=fuzzy_matcher,
        default_fallback_url=current_app.config['DEFAULT_FALLBACK_URL']
    )

    # If we have a direct URL, redirect to it
    if result.url:
        return redirect(result.url, code=302)

    # If we have suggestions, show them to the user
    if result.suggestions:
        return render_template('suggestions.html',
                             query=query,
                             suggestions=result.suggestions)

    # This shouldn't happen, but just in case, redirect to Google
    return redirect(f"https://www.google.com/search?q={query}", code=302)
