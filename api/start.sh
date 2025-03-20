#!/usr/bin/env bash

set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Add custom CA certificates
if [[ -n "${CA_CERTIFICATES:-}" ]]; then
    echo "${CA_CERTIFICATES}" >> /usr/local/share/ca-certificates/custom-user-cert.crt
    update-ca-certificates
fi

# Run DB migrations
python3 /app/api/src/manage.py migrate
# Collect static files (of custom plugins)
python3 /app/api/src/manage.py collectstatic --noinput --no-post-process
# Start web application
gunicorn --bind=:8000 \
         --worker-class=uvicorn.workers.UvicornWorker \
         --workers=${SERVER_WORKERS:-4} \
         --max-requests=1000 \
         --max-requests-jitter=100 \
         --graceful-timeout=${SERVER_WORKER_RESTART_TIMEOUT:-3600} \
         sysreptor.conf.asgi:application
