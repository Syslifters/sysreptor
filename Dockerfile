FROM --platform=$BUILDPLATFORM node:20-alpine3.19 AS pdfviewer-dev

# Install dependencies
WORKDIR /app/packages/pdfviewer/
COPY packages/pdfviewer/package.json packages/pdfviewer/package-lock.json /app/packages/pdfviewer//
RUN npm install

FROM --platform=$BUILDPLATFORM pdfviewer-dev AS pdfviewer
# Build JS bundle
COPY packages/pdfviewer /app/packages/pdfviewer//
RUN npm run build




FROM --platform=$BUILDPLATFORM node:20-alpine3.19 AS frontend-dev

ENV NODE_OPTIONS="--max-old-space-size=4096"

# Install dependencies
WORKDIR /app/packages/markdown/
COPY packages/markdown/package.json packages/markdown/package-lock.json /app/packages/markdown/
RUN npm install

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json /app/frontend/
RUN npm install


FROM --platform=$BUILDPLATFORM frontend-dev AS frontend-test
# Include source code
COPY packages/markdown/ /app/packages/markdown/
COPY frontend /app/frontend/
COPY api/src/reportcreator_api/tasks/rendering/global_assets /app/frontend/src/assets/rendering/
COPY --from=pdfviewer /app/packages/pdfviewer/dist/ /app/frontend/src/public/static/pdfviewer/

# Test command
CMD ["npm", "run", "test"]


FROM --platform=$BUILDPLATFORM frontend-test AS frontend
# Build JS bundle
RUN npm run generate







FROM --platform=$BUILDPLATFORM node:20-alpine3.19 AS rendering-dev

# Install dependencies
WORKDIR /app/packages/markdown/
COPY packages/markdown/package.json packages/markdown/package-lock.json /app/packages/markdown/
RUN npm install

WORKDIR /app/rendering/
COPY rendering/package.json rendering/package-lock.json /app/rendering/
RUN npm install


FROM --platform=$BUILDPLATFORM rendering-dev AS rendering
# Include source code
COPY rendering /app/rendering/
COPY packages/markdown/ /app/packages/markdown/
# Build JS bundle
RUN npm run build




FROM python:3.12-slim-bookworm AS api-dev

# Get a list a preinstalled apt packages
RUN mkdir /src && \
    chown 1000:1000 /src && \
    dpkg-query -W -f='${binary:Package}=${Version}\n' > /src/pre_installed.txt && \
    echo "This image distributes binaries of copyleft licensed software. Please find the corresponding source code in our source-code distributing images (append `-src` to the image tags; e.g. syslifters/sysreptor:2024.58-src)." > /src/SOURCES.txt

# Install system dependencies required by weasyprint and chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        curl \
        fontconfig \
        fonts-noto \
        fonts-noto-mono \
        fonts-noto-ui-core \
        fonts-noto-color-emoji \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        ghostscript \
        gpg \
        gpg-agent \
        libharfbuzz-subset0 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        unzip \
        wget \
        postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install fonts
COPY api/fonts /usr/share/fonts/truetype/
RUN mv /usr/share/fonts/truetype/fontconfig.conf /etc/fonts/conf.d/00-sysreptor-fonts.conf && \
    rm -rf /usr/share/fonts/truetype/dejavu/ && \
    rm -f /etc/fonts/conf.d/*dejavu* && \
    fc-cache -f

# Install python packages
ENV PYTHONUNBUFFERED=on \
    PYTHONDONTWRITEBYTECODE=on \
    CHROMIUM_EXECUTABLE=/usr/lib/chromium/chromium \
    GHOSTSCRIPT_EXECUTABLE=/usr/bin/gs \
    PATH=$PATH:/root/.local/bin \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt


WORKDIR /app/api/
COPY api/pyproject.toml api/poetry.lock /app/api/
RUN --mount=type=cache,target=/root/.cache/ \
    pip install --no-cache poetry==1.8.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-cache --no-interaction --no-root

# Unprivileged user
RUN useradd --uid=1000 --create-home --shell=/bin/bash user \
    && mkdir -p /data /app/api && chown user:user /data /app/api
USER 1000
VOLUME [ "/data" ]

# Configure application
ARG VERSION=dev
ENV VERSION=${VERSION} \
    DEBUG=off \
    MEDIA_ROOT=/data/ \
    SERVER_WORKERS=4 \
    PDF_RENDER_SCRIPT_PATH=/app/rendering/dist/bundle.js

# Start server
EXPOSE 8000
CMD ["/bin/bash", "/app/api/start.sh"]



FROM --platform=$BUILDPLATFORM api-dev AS api-prebuilt

# Copy source code (including pre-build static files)
COPY --chown=user:user api/src /app/api/
COPY --chown=user:user rendering/dist /app/rendering/dist/



FROM --platform=$BUILDPLATFORM api-dev AS api-test
# Copy source code
COPY --chown=user:user api/src /app/api/

# Copy generated template rendering script
COPY --from=rendering --chown=user:user /app/rendering/dist /app/rendering/dist/


FROM --platform=$BUILDPLATFORM api-test AS api-statics
# Generate static frontend files
# Post-process django files (for admin, API browser) and post-process them (e.g. add unique file hash)
# Do not post-process nuxt files, because they already have hash names (and django failes to post-process them)
RUN python3 manage.py collectstatic --no-input --clear
COPY --from=frontend /app/frontend/dist/index.html /app/frontend/dist/static/ /app/api/frontend/static/
RUN mv /app/api/frontend/static/index.html /app/api/frontend/index.html \
    && python3 manage.py collectstatic --no-input --no-post-process \
    && python3 -m whitenoise.compress /app/api/static/ map



FROM api-test AS api
COPY --from=api-statics /app/api/frontend/index.html /app/api/frontend/index.html
COPY --from=api-statics /app/api/static/ /app/api/static/
USER 0
COPY --chown=1000:1000 api/generate_notice.sh api/download_sources.sh api/start.sh api/NOTICE /app/api/
RUN /bin/bash /app/api/generate_notice.sh
# Copy of changelog should be one of the last things to use cache for prod releases
COPY LICENSE CHANGELOG.md /app/
USER 1000




FROM api AS api-src
USER 0
RUN dpkg-query -W -f='${binary:Package}=${Version}\n' > /src/post_installed.txt \
    && bash /app/api/download_sources.sh
USER 1000