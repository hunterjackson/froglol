from flask import Blueprint, request, jsonify
from app.models import Bookmark, Alias
from app import db

bp = Blueprint("bookmarks", __name__, url_prefix="/api")


@bp.route("/bookmarks", methods=["GET"])
def get_bookmarks():
    """Get all bookmarks."""
    bookmarks = Bookmark.query.order_by(Bookmark.name).all()
    return jsonify([bookmark.to_dict() for bookmark in bookmarks])


@bp.route("/bookmarks/<int:bookmark_id>", methods=["GET"])
def get_bookmark(bookmark_id):
    """Get a specific bookmark."""
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    return jsonify(bookmark.to_dict())


@bp.route("/bookmarks", methods=["POST"])
def create_bookmark():
    """Create a new bookmark."""
    data = request.get_json()

    if not data or not data.get("name") or not data.get("url"):
        return jsonify({"error": "Name and URL are required"}), 400

    # Check if name already exists
    existing = Bookmark.query.filter_by(name=data["name"].lower()).first()
    if existing:
        return jsonify({"error": "Bookmark with this name already exists"}), 400

    bookmark = Bookmark(
        name=data["name"].lower(),
        url=data["url"],
        description=data.get("description", ""),
    )

    db.session.add(bookmark)
    db.session.commit()

    # Add aliases if provided
    if data.get("aliases"):
        for alias_name in data["aliases"]:
            if alias_name and alias_name.strip():
                alias = Alias(alias=alias_name.lower().strip(), bookmark_id=bookmark.id)
                db.session.add(alias)

        db.session.commit()

    return jsonify(bookmark.to_dict()), 201


@bp.route("/bookmarks/<int:bookmark_id>", methods=["PUT"])
def update_bookmark(bookmark_id):
    """Update an existing bookmark."""
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update fields if provided
    if "name" in data:
        # Check if new name conflicts with existing bookmark
        existing = Bookmark.query.filter_by(name=data["name"].lower()).first()
        if existing and existing.id != bookmark_id:
            return jsonify({"error": "Bookmark with this name already exists"}), 400
        bookmark.name = data["name"].lower()

    if "url" in data:
        bookmark.url = data["url"]

    if "description" in data:
        bookmark.description = data["description"]

    db.session.commit()
    return jsonify(bookmark.to_dict())


@bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def delete_bookmark(bookmark_id):
    """Delete a bookmark (and its aliases via cascade)."""
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    db.session.delete(bookmark)
    db.session.commit()
    return "", 204


@bp.route("/bookmarks/<int:bookmark_id>/aliases", methods=["POST"])
def add_alias(bookmark_id):
    """Add an alias to a bookmark."""
    # Verify bookmark exists (raises 404 if not)
    Bookmark.query.get_or_404(bookmark_id)
    data = request.get_json()

    if not data or not data.get("alias"):
        return jsonify({"error": "Alias is required"}), 400

    alias_name = data["alias"].lower().strip()

    # Check if alias already exists
    existing = Alias.query.filter_by(alias=alias_name).first()
    if existing:
        return jsonify({"error": "Alias already exists"}), 400

    # Check if alias conflicts with bookmark name
    existing_bookmark = Bookmark.query.filter_by(name=alias_name).first()
    if existing_bookmark:
        return jsonify({"error": "Alias conflicts with existing bookmark name"}), 400

    alias = Alias(alias=alias_name, bookmark_id=bookmark_id)
    db.session.add(alias)
    db.session.commit()

    return jsonify(alias.to_dict()), 201


@bp.route("/aliases/<int:alias_id>", methods=["DELETE"])
def delete_alias(alias_id):
    """Delete an alias."""
    alias = Alias.query.get_or_404(alias_id)
    db.session.delete(alias)
    db.session.commit()
    return "", 204
