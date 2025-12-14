import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_class="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes import redirect, bookmarks, ui

    app.register_blueprint(redirect.bp)
    app.register_blueprint(bookmarks.bp)
    app.register_blueprint(ui.bp)

    # Check if database file exists (for SQLite)
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    is_first_run = False

    # Only auto-seed for file-based SQLite databases (not in-memory or testing)
    if db_uri.startswith("sqlite:///") and not app.config.get("TESTING", False):
        db_path = db_uri.replace("sqlite:///", "")
        # Don't auto-seed for in-memory databases
        if db_path and db_path != ":memory:":
            is_first_run = not os.path.exists(db_path)

    # Create database tables
    with app.app_context():
        db.create_all()

        # Seed database on first run
        if is_first_run:
            from app.seed import seed_initial_data

            seed_initial_data()
            print("Database seeded with initial bookmarks!")

    return app
