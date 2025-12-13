# Froglol Docker Deployment Guide

This guide covers deploying Froglol using Docker and Docker Compose.

## Quick Start

```bash
# Clone and enter directory
git clone <repo-url>
cd froglol

# Start with Docker Compose
docker compose up -d

# Access at http://localhost:5000
```

## Architecture

### Components
- **Base Image**: Python 3.11 slim (minimal footprint)
- **WSGI Server**: Gunicorn with 2 workers
- **Database**: SQLite (persisted via volume mount)
- **Port**: 5000 (configurable)

### Resource Configuration

**Default Limits (suitable for few users):**
- CPU: 0.5 cores max (0.25 reserved)
- Memory: 256MB max (128MB reserved)
- Workers: 2 Gunicorn workers
- Worker connections: 100 per worker

**Adjust for more users** in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Increase for more concurrent users
      memory: 512M     # More memory for larger datasets
```

And in `gunicorn.conf.py`:
```python
workers = 4  # Rule of thumb: (2 x CPU cores) + 1
```

## Configuration

### Environment Variables

Create a `.env` file (optional):
```bash
SECRET_KEY=your-strong-random-secret-key
DATABASE_URL=sqlite:///instance/froglol.db
DEFAULT_FALLBACK_URL=https://www.google.com/search?q=%s
FUZZY_MATCH_THRESHOLD=60
FUZZY_MATCH_LIMIT=3
```

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Volume Mounts

The `instance` directory is mounted to persist the SQLite database:
```yaml
volumes:
  - ./instance:/app/instance
```

**Important**: Ensure this directory has proper permissions:
```bash
mkdir -p instance
chmod 755 instance
```

## Management

### Using Makefile (Recommended)

```bash
make up          # Start application
make down        # Stop application
make logs        # View logs (follow mode)
make restart     # Restart application
make clean       # Remove all data and containers
make shell       # Access container shell
make stats       # View resource usage
make test        # Run tests in container
```

### Manual Docker Compose Commands

```bash
# Start
docker compose up -d

# View logs
docker compose logs -f froglol

# Stop
docker compose down

# Restart
docker compose restart

# Rebuild
docker compose up -d --build

# Execute commands in container
docker compose exec froglol python -c "from app.models import Bookmark; print(Bookmark.query.count())"
```

## Health Checks

The container includes automatic health checks:
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Start period**: 10 seconds
- **Retries**: 3 attempts

Check container health:
```bash
docker compose ps
docker inspect froglol | grep -A 10 Health
```

## Monitoring

### View Logs
```bash
# Follow logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Only errors
docker compose logs | grep ERROR
```

### Resource Usage
```bash
# Real-time stats
docker stats froglol

# One-time snapshot
docker stats --no-stream froglol
```

### Database Size
```bash
ls -lh instance/froglol.db
```

## Backup and Restore

### Backup Database
```bash
# While container is running
docker compose exec froglol sqlite3 /app/instance/froglol.db .dump > backup.sql

# Or simply copy the file
cp instance/froglol.db instance/froglol.db.backup
```

### Restore Database
```bash
# Stop container
docker compose down

# Restore backup
cp instance/froglol.db.backup instance/froglol.db

# Start container
docker compose up -d
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs

# Verify permissions
ls -la instance/

# Check if port is in use
sudo netstat -tlnp | grep 5000
```

### Database Locked Error
```bash
# Stop all containers
docker compose down

# Remove lock file
rm -f instance/froglol.db-*

# Restart
docker compose up -d
```

### Reset Everything
```bash
# Nuclear option: remove all data
make clean
# OR
docker compose down -v
rm -rf instance/
```

## Production Deployment

### Behind Reverse Proxy (Nginx)

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name froglol.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### With SSL/TLS (Caddy)

Caddy automatically handles HTTPS:
```caddyfile
froglol.example.com {
    reverse_proxy localhost:5000
}
```

### Docker Compose Override

Create `docker-compose.override.yml` for local customization:
```yaml
version: '3.8'

services:
  froglol:
    ports:
      - "8080:5000"  # Different port
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

## Scaling Considerations

### When to Scale Up

Monitor these metrics:
- CPU usage consistently > 70%
- Memory usage > 80%
- Response times > 500ms
- Queue lengths increasing

### Scaling Options

1. **Vertical Scaling** (more resources per container):
   - Increase CPU/memory limits
   - Add more Gunicorn workers

2. **Horizontal Scaling** (multiple containers):
   - Use a load balancer
   - Migrate to PostgreSQL for concurrent writes
   - Share `instance` directory or use separate databases

## Security Checklist

- [ ] Set strong `SECRET_KEY` in production
- [ ] Deploy behind HTTPS reverse proxy
- [ ] Keep Docker images updated
- [ ] Regular database backups
- [ ] Monitor container logs for suspicious activity
- [ ] Use Docker networks for isolation
- [ ] Limit container capabilities
- [ ] Regular security updates

## Performance Tuning

### Gunicorn Workers

Formula: `workers = (2 × CPU_cores) + 1`

For CPU-bound workloads:
```python
# gunicorn.conf.py
workers = 2
worker_class = "sync"
```

For I/O-bound workloads:
```python
# gunicorn.conf.py
workers = 4
worker_class = "gevent"  # Requires: pip install gevent
```

### Database Optimization

SQLite is sufficient for small deployments. For better performance:
```bash
# Enable WAL mode (already enabled by default)
sqlite3 instance/froglol.db "PRAGMA journal_mode=WAL;"

# Optimize database
sqlite3 instance/froglol.db "VACUUM;"
```

## Support

For issues or questions:
1. Check logs: `docker compose logs`
2. Verify configuration: `docker compose config`
3. Test locally without Docker first
4. Review GitHub issues
