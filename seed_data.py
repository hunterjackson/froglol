from app import create_app, db
from app.models import Bookmark, Alias
from app.seed import seed_initial_data, SEED_BOOKMARKS


def seed_database():
    """Populate database with initial bookmarks (clears existing data first)."""
    app = create_app()

    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        Alias.query.delete()
        Bookmark.query.delete()
        db.session.commit()

        # Add seed bookmarks
        print("Adding seed bookmarks...")
        seed_initial_data()

        # Print what was added
        for bookmark_data in SEED_BOOKMARKS:
            print(f"  Added: {bookmark_data['name']} ({', '.join(bookmark_data.get('aliases', []))})")

        print(f"\nSuccessfully seeded {len(SEED_BOOKMARKS)} bookmarks!")


if __name__ == '__main__':
    seed_database()
