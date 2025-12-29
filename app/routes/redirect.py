from flask import Blueprint, request, redirect, render_template, url_for
from app.services.redirect_service import process_redirect

bp = Blueprint("redirect", __name__)


@bp.route("/")
def index():
    """
    Main redirect endpoint.
    Receives query from browser search bar and redirects to appropriate URL.
    """
    query = request.args.get("q", "")

    # Process the redirect
    result = process_redirect(query)

    # If we have a direct URL, redirect to it
    if result.url:
        return redirect(result.url, code=302)

    # No match found - show error page
    return render_template("no_match.html", query=query), 404
