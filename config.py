import os
from dotenv import load_dotenv

load_dotenv()

# Get the base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(basedir, "instance", "froglol.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_FALLBACK_URL = os.getenv('DEFAULT_FALLBACK_URL', 'https://www.google.com/search?q=%s')
    FUZZY_MATCH_THRESHOLD = int(os.getenv('FUZZY_MATCH_THRESHOLD', '60'))
    FUZZY_MATCH_LIMIT = int(os.getenv('FUZZY_MATCH_LIMIT', '3'))
