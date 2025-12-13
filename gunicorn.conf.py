# Gunicorn configuration file

# Server socket
bind = "0.0.0.0:5000"
backlog = 64

# Worker processes
workers = 1
worker_class = "sync"
worker_connections = 100
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "froglol"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
keyfile = None
certfile = None
