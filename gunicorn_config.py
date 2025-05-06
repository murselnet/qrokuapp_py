import multiprocessing

# Gunicorn yapılandırması
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"