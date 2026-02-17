# gunicorn.conf.py
from multiprocessing import cpu_count

bind = "127.0.0.1:8000"
workers = 2 * cpu_count() + 1
worker_class = 'gunicorn.workers.sync.SyncWorker'  # Меняем на WSGI worker
keepalive = 65
timeout = 120