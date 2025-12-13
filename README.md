# Froglol

A URL bookmark redirection server inspired by Facebook's bunnylol. Froglol allows you to create custom shortcuts for your favorite websites and use them directly from your browser's URL bar.

## Features

- **Fast URL Redirection**: Type shortcuts in your browser's address bar to quickly navigate to websites
- **Dynamic Search Integration**: Use placeholders in URLs to pass search queries (e.g., `google python tutorials`)
- **Command Aliases**: Create multiple shortcuts for the same bookmark (e.g., `g` and `google`)
- **Fuzzy Matching**: Get up to 3 suggestions when you mistype a command
- **Web UI**: Manage bookmarks through a clean, intuitive interface
- **Usage Tracking**: See which bookmarks you use most frequently
- **Auto-Seeding**: Automatically sets up 8 common bookmarks on first run

## Example Usage

Once set up as your browser's search engine:

- Type `google anthropic` → Redirects to Google search for "anthropic"
- Type `gh flask` → Redirects to GitHub search for "flask"
- Type `yt music` → Redirects to YouTube search for "music"
- Type `googl` (typo) → Shows suggestions: "Did you mean 'google'?"

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd froglol
```

### 2. Set up the Python environment with uv

```bash
uv venv
uv pip install -r requirements.txt
```

### 3. (Optional) Create environment file

Copy `.env.example` to `.env` and customize settings:

```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/froglol.db
DEFAULT_FALLBACK_URL=https://www.google.com/search?q=%s
FUZZY_MATCH_THRESHOLD=60
FUZZY_MATCH_LIMIT=3
```

### 4. Run the application

```bash
uv run python run.py
```

The server will start at `http://localhost:5000`

**Note**: On first run, the database will be automatically created and seeded with 12 bookmarks including:
- Froglol management page (`manage`, `list`)
- Search engines: Google, GitHub, YouTube, Wikipedia, Stack Overflow, Reddit, Twitter, Amazon
- AI chatbots: ChatGPT, Claude, Gemini

## Docker Deployment (Recommended for Production)

### Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd froglol
   ```

2. **(Optional) Set environment variables**
   ```bash
   cp .env.example .env
   # Edit .env to set your SECRET_KEY
   ```

3. **Start the application**
   ```bash
   docker compose up -d
   ```

The application will be available at `http://localhost:5000`

### Docker Commands

**Using Make (recommended):**
```bash
make up          # Start the application
make logs        # View logs
make down        # Stop the application
make restart     # Restart the application
make clean       # Stop and remove everything
make shell       # Open shell in container
make stats       # View resource usage
```

**Using Docker Compose directly:**
```bash
# Start in detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop the application
docker compose down

# Rebuild after code changes
docker compose up -d --build

# View resource usage
docker stats froglol
```

### Resource Limits

The Docker setup includes resource constraints suitable for a small user base:
- **CPU**: 0.5 cores max (0.25 reserved)
- **Memory**: 256MB max (128MB reserved)
- **Workers**: 2 Gunicorn workers
- **Connections**: 100 per worker

These limits are perfect for a few concurrent users. Adjust in `docker-compose.yml` if needed.

### Database Persistence

The SQLite database is stored in the `./instance` directory, which is mounted as a Docker volume. Your data persists across container restarts.

To reset the database:
```bash
docker compose down
rm -rf instance/froglol.db
docker compose up -d  # Will auto-seed on startup
```

## Browser Setup

### Chrome, Edge, or Brave

1. Go to **Settings** → **Search engine** → **Manage search engines**
2. Click **Add** next to "Site search"
3. Fill in the form:
   - **Search engine**: `froglol`
   - **Shortcut**: `f` (or any keyword you prefer)
   - **URL**: `http://localhost:5000/?q=%s`
4. Click **Add**
5. (Optional) Set froglol as your default search engine

### Using Froglol

- **Direct activation**: Type `f` (or your chosen keyword) in the address bar, press Tab or Space
- **As default**: If set as default, just type your commands directly

## Managing Bookmarks

### Web Interface

Visit `http://localhost:5000/manage` to:
- View all bookmarks
- Create new bookmarks
- Edit existing bookmarks
- Delete bookmarks
- Add/remove aliases

### Creating a Bookmark

1. Go to `http://localhost:5000/manage/new`
2. Fill in the form:
   - **Command Name**: The shortcut you'll type (e.g., `google`)
   - **URL Template**: The URL with `%s` placeholder (e.g., `https://www.google.com/search?q=%s`)
   - **Description**: Optional description
   - **Aliases**: Optional comma-separated shortcuts (e.g., `g, search`)
3. Click **Create Bookmark**

### URL Template Format

The URL template can optionally contain `%s` where search arguments will be inserted:

- `https://www.google.com/search?q=%s`
- `https://github.com/search?q=%s`
- `https://www.amazon.com/s?k=%s`

## API Endpoints

### Bookmarks

- `GET /api/bookmarks` - List all bookmarks
- `GET /api/bookmarks/<id>` - Get specific bookmark
- `POST /api/bookmarks` - Create new bookmark
- `PUT /api/bookmarks/<id>` - Update bookmark
- `DELETE /api/bookmarks/<id>` - Delete bookmark

### Aliases

- `POST /api/bookmarks/<id>/aliases` - Add alias to bookmark
- `DELETE /api/aliases/<id>` - Remove alias

## Project Structure

```
froglol/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── routes/
│   │   ├── redirect.py          # Main redirection logic
│   │   ├── bookmarks.py         # Bookmark API
│   │   └── ui.py                # Web UI routes
│   ├── services/
│   │   ├── redirect_service.py  # Redirect business logic
│   │   └── fuzzy_matcher.py     # Fuzzy matching
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── bookmark_form.html
│       └── suggestions.html
├── tests/                        # Test files
├── instance/                     # SQLite database (gitignored)
├── config.py                     # Configuration
├── requirements.txt              # Dependencies
├── run.py                        # Entry point
├── seed_data.py                  # Database seeding script
└── README.md
```

## Development

### Running Tests

```bash
uv run pytest
```

### Database Management

The SQLite database is **automatically created and seeded** when you first run the application. It's stored in `instance/froglol.db`.

**Automatic Seeding**: On first run, the database is populated with 8 common bookmarks. The app detects if the database exists, so it won't re-seed on subsequent runs.

To manually reset and re-seed the database:

```bash
rm -f instance/froglol.db
uv run python seed_data.py
```

Or simply restart the app after deleting the database file - it will auto-seed again.

## Configuration

All configuration is in `config.py` and can be overridden with environment variables:

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string
- `DEFAULT_FALLBACK_URL`: Where to redirect when no bookmark matches
- `FUZZY_MATCH_THRESHOLD`: Minimum similarity score (0-100) for suggestions
- `FUZZY_MATCH_LIMIT`: Maximum number of suggestions to show

## Security Considerations

### General Security
- URLs are properly encoded to prevent injection attacks
- Only HTTP and HTTPS schemes are recommended for bookmark URLs
- User input is sanitized and validated before database storage
- For production use, always set a strong `SECRET_KEY`

### Docker Security Features
- **Non-root user**: Container runs as user `froglol` (UID 1000)
- **Read-only filesystem**: Root filesystem is read-only except for necessary tmpfs mounts
- **No new privileges**: Container cannot gain additional privileges
- **Resource limits**: CPU and memory constraints prevent resource exhaustion
- **Health checks**: Automatic container health monitoring

### Production Recommendations
1. **Use HTTPS**: Deploy behind a reverse proxy (nginx/Caddy) with SSL/TLS
2. **Strong secrets**: Generate SECRET_KEY with `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Network isolation**: Use Docker networks to isolate the container
4. **Regular updates**: Keep Docker images and dependencies updated
5. **Backups**: Regularly backup the `instance/froglol.db` file

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

Inspired by Facebook's internal bunnylol project, which allows employees to quickly navigate to internal tools and resources.
