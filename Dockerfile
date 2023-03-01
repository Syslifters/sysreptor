FROM node:16-alpine AS pdfviewer-dev
WORKDIR /app/packages/pdfviewer/
COPY packages/pdfviewer/package.json packages/pdfviewer/package-lock.json /app/packages/pdfviewer//
RUN npm install

FROM pdfviewer-dev AS pdfviewer
COPY packages/pdfviewer /app/packages/pdfviewer//
RUN npm run build







FROM node:16-alpine AS frontend-dev

WORKDIR /app/packages/markdown/
COPY packages/markdown/package.json packages/markdown/package-lock.json /app/packages/markdown/
RUN npm install

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json /app/frontend/
RUN npm install


FROM frontend-dev AS frontend-test
COPY packages/markdown/ /app/packages/markdown/
COPY frontend /app/frontend/
COPY --from=pdfviewer /app/packages/pdfviewer/dist/ /app/frontend/static/static/pdfviewer/
CMD npm run test


FROM frontend-test AS frontend
RUN npm run build







FROM node:16-alpine AS rendering-dev

WORKDIR /app/packages/markdown/
COPY packages/markdown/package.json packages/markdown/package-lock.json /app/packages/markdown/
RUN npm install

WORKDIR /app/rendering/
COPY rendering/package.json rendering/package-lock.json /app/rendering/
RUN npm install


FROM rendering-dev AS rendering
COPY rendering /app/rendering/
COPY packages/markdown/ /app/packages/markdown/
RUN npm run build





FROM python:3.10-slim-bullseye AS rendering-worker-dev

# Install system dependencies required by PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        fontconfig \
        fonts-noto \
        fonts-noto-mono \
        fonts-noto-ui-core \
        fonts-open-sans \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        unzip \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install fonts
WORKDIR /app/rendering-worker/
COPY rendering-worker/download_fonts.sh /app/rendering-worker/download_fonts.sh
RUN chmod +x /app/rendering-worker/download_fonts.sh && /app/rendering-worker/download_fonts.sh

# Install python packages
ENV PYTHONUNBUFFERED=on \
    PYTHONDONTWRITEBYTECODE=on
COPY rendering-worker/requirements.txt /app/rendering-worker/requirements.txt
RUN pip install -r /app/rendering-worker/requirements.txt

# Configure playwright
ENV CHROMIUM_EXECUTABLE=/usr/lib/chromium/chromium


FROM rendering-worker-dev AS rendering-worker
# Copy source code
COPY rendering-worker/src /app/rendering-worker/

# Copy generated template rendering script
COPY --from=rendering /app/rendering/dist /app/rendering/dist/
ENV PDF_RENDER_SCRIPT_PATH=/app/rendering/dist/bundle.js

USER 1000

CMD celery --app=reportcreator_rendering.celery --quiet worker -Q reportcreator_rendering





FROM python:3.10-slim-bullseye AS api-dev

# Install system dependencies required by weasyprint and chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        curl \
        fontconfig \
        fonts-noto \
        fonts-noto-mono \
        fonts-noto-ui-core \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        unzip \
        wget \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install fonts
WORKDIR /app/api/
COPY api/download_fonts.sh /app/api/download_fonts.sh
RUN chmod +x /app/api/download_fonts.sh && /app/api/download_fonts.sh

# Install python packages
ENV PYTHONUNBUFFERED=on \
    PYTHONDONTWRITEBYTECODE=on \
    CHROMIUM_EXECUTABLE=/usr/lib/chromium/chromium \
    DJANGO_SETTINGS_MODULE=reportcreator_api.conf.settings
WORKDIR /app/api/
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install -r /app/api/requirements.txt



FROM api-dev AS api-test
# Copy source code
COPY api/src /app/api
# Copy generated template rendering script
COPY --from=rendering /app/rendering/dist /app/rendering/dist/
ENV PDF_RENDER_SCRIPT_PATH=/app/rendering/dist/bundle.js

CMD pytest



FROM api-test as api
# Generate static frontend files
# Post-process django files (for admin, API browser) and post-process them (e.g. add unique file hash)
# Do not post-process nuxt files, because they already have hash names (and django failes to post-process them)
RUN python3 manage.py collectstatic --no-input --clear
COPY --from=frontend /app/frontend/dist/ /app/api/frontend/
RUN python3 manage.py collectstatic --no-input --no-post-process \
    && python3 -m whitenoise.compress /app/api/frontend/ /app/api/static/

# Configure application
ENV DEBUG=off \
    MEDIA_ROOT=/data/ \
    SERVER_WORKERS=4

RUN mkdir /data && chown 1000:1000 /data && chmod 777 /data
VOLUME [ "/data" ]

# Copy changelog
COPY CHANGELOG.md /app/

# Start server
USER 1000
EXPOSE 8000
CMD python3 manage.py migrate && \
    gunicorn \
        --bind=:8000 --worker-class=uvicorn.workers.UvicornWorker --workers=${SERVER_WORKERS} \
        --max-requests=500 --max-requests-jitter=100 \
        reportcreator_api.conf.asgi:application
