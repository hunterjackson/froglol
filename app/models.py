from datetime import datetime
from app import db


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    url = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    use_count = db.Column(db.Integer, default=0)

    # Relationship to aliases
    aliases = db.relationship('Alias', backref='bookmark', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Bookmark {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'use_count': self.use_count,
            'aliases': [alias.alias for alias in self.aliases],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Alias(db.Model):
    __tablename__ = 'aliases'

    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(255), unique=True, nullable=False, index=True)
    bookmark_id = db.Column(db.Integer, db.ForeignKey('bookmarks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Alias {self.alias}>'

    def to_dict(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'bookmark_id': self.bookmark_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
