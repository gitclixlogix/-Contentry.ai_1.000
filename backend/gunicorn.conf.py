"""
Gunicorn Configuration for Production Scalability
Optimized for 100K+ concurrent users

Run with: gunicorn -c gunicorn.conf.py server:app
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8001"
backlog = 2048

# Worker processes
# Rule of thumb: (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Worker connections (for async workers)
worker_connections = 1000

# Timeout settings
timeout = 120  # Kill worker if no response in 120s
graceful_timeout = 30  # Time to finish requests on restart
keepalive = 5  # Keep connection open for 5s between requests

# Process naming
proc_name = "contentry-api"

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# Performance tuning
max_requests = 10000  # Restart worker after N requests (prevents memory leaks)
max_requests_jitter = 1000  # Add randomness to prevent all workers restarting at once

# Pre-fork hooks
def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker is forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking master process")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    worker.log.info("Worker interrupted")

def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    worker.log.info("Worker aborted")

def on_exit(server):
    """Called just before exiting gunicorn."""
    server.log.info("Server shutting down")


# =============================================================================
# SCALING GUIDELINES
# =============================================================================
# 
# Current setup (single server, 8 cores):
#   - Workers: 17 (8 * 2 + 1)
#   - Estimated capacity: ~8,000-10,000 concurrent users
#   - RPS: ~2,000-3,000
#
# To scale further:
#   1. Add more servers behind load balancer
#   2. Each server can handle ~10K concurrent users
#   3. For 100K users: ~10-12 servers recommended
#
# Memory requirements per server:
#   - Base: ~500MB
#   - Per worker: ~100-200MB
#   - Total: ~2-4GB for 17 workers
#
# =============================================================================
