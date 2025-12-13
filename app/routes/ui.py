from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Bookmark, Alias
from app import db

bp = Blueprint('ui', __name__, url_prefix='/manage')


@bp.route('/')
def manage():
    """Show the bookmark management interface."""
    bookmarks = Bookmark.query.order_by(Bookmark.use_count.desc(), Bookmark.name).all()
    return render_template('index.html', bookmarks=bookmarks)


@bp.route('/new')
def new_bookmark():
    """Show form to create a new bookmark."""
    return render_template('bookmark_form.html', bookmark=None)


@bp.route('/edit/<int:bookmark_id>')
def edit_bookmark(bookmark_id):
    """Show form to edit an existing bookmark."""
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    return render_template('bookmark_form.html', bookmark=bookmark)
