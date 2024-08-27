#!/bin/bash
if [[ -n "$CA_CERTIFICATES" ]]; then
    echo "${CA_CERTIFICATES}" >> /usr/local/share/ca-certificates/custom-user-cert.crt
    update-ca-certificates
fi

python3 manage.py migrate
gunicorn --bind=:8000 \
         --worker-class=uvicorn.workers.UvicornWorker \
         --workers=${SERVER_WORKERS} \
         --max-requests=500 \
         --max-requests-jitter=100 \
         --graceful-timeout=300 \
         reportcreator_api.conf.asgi:application
