"""Gunicorn settings. Change them per ECS deploy with env vars (Phase 6 experiments)."""
import os

bind = "0.0.0.0:8000"                                     # listen on all interfaces inside the container
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))    # separate processes (each has its own DB connection/pool)
threads = int(os.environ.get("GUNICORN_THREADS", "1"))    # >1 = threads inside each worker share its pool
worker_class = "gthread" if threads > 1 else "sync"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))   # kill a request stuck longer than this

accesslog = "-"                                           # "-" = stdout -> CloudWatch Logs
errorlog = "-"

# Max possible Postgres connections from ONE task:
#   CONN_MAX_AGE mode: workers x threads
#   DB_POOL mode:      workers x DB_POOL_MAX
