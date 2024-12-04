# Globally defined ARGS
ARG TESTED_API_IMAGE=undefined_test_image_used_in_ci
ARG PROD_API_IMAGE=undefined_prod_image_used_in_ci



FROM --platform=$BUILDPLATFORM node:20-alpine3.19 AS frontend-dev
ENV NODE_OPTIONS="--max-old-space-size=4096"
WORKDIR /app/packages/


FROM --platform=$BUILDPLATFORM frontend-dev AS frontend-base
# Copy package.json files of all packages
COPY packages/package.json packages/package-lock.json /app/packages/
COPY packages/frontend/package.json /app/packages/frontend/
COPY packages/markdown/package.json /app/packages/markdown/
COPY packages/pdfviewer/package.json /app/packages/pdfviewer/
COPY packages/nuxt-base-layer/package.json /app/packages/nuxt-base-layer/
COPY packages/plugin-base-layer/package.json /app/packages/plugin-base-layer/
COPY packages/rendering/package.json /app/packages/rendering/
# Install dependencies of all packages
RUN npm install




FROM --platform=$BUILDPLATFORM frontend-base AS pdfviewer
# Build JS bundle
COPY packages/pdfviewer /app/packages/pdfviewer/
WORKDIR /app/packages/pdfviewer/
RUN npm run build


FROM --platform=$BUILDPLATFORM frontend-base AS rendering
# Include source code
COPY packages/markdown /app/packages/markdown/
COPY packages/rendering /app/packages/rendering/
# Build JS bundle
WORKDIR /app/packages/rendering/
RUN npm run build




FROM --platform=$BUILDPLATFORM frontend-base AS frontend-test
# Include source code
COPY packages/markdown /app/packages/markdown/
COPY packages/nuxt-base-layer /app/packages/nuxt-base-layer/
COPY packages/frontend /app/packages/frontend/
COPY api/src/reportcreator_api/tasks/rendering/global_assets /app/packages/frontend/src/assets/rendering/
COPY --from=pdfviewer /app/packages/pdfviewer/dist/ /app/packages/nuxt-base-layer/src/public/static/pdfviewer/dist/
# Test command
WORKDIR /app/packages/frontend/
CMD ["npm", "run", "test"]


FROM --platform=$BUILDPLATFORM frontend-test AS frontend
# Build JS bundle
RUN npm run postinstall && npm run generate




FROM --platform=$BUILDPLATFORM frontend-dev AS plugin-builder-dev
RUN apk add --no-cache \
    bash \
    git \
    curl \
    wget \
    unzip \ 
    jq \
    inotify-tools
WORKDIR /app/plugins/

FROM --platform=$BUILDPLATFORM plugin-builder-dev AS plugin-builder
# Copy installed node_modules
COPY --from=frontend-base /app/packages /app/packages/
# Copy source code
COPY packages/nuxt-base-layer /app/packages/nuxt-base-layer/
COPY --from=pdfviewer /app/packages/pdfviewer/dist/ /app/packages/nuxt-base-layer/src/public/static/pdfviewer/dist/
COPY packages/plugin-base-layer /app/packages/plugin-base-layer/
COPY packages/markdown /app/packages/markdown/
COPY plugins /app/plugins/
# Build plugins
RUN /app/plugins/build.sh




FROM python:3.12-slim-bookworm AS api-dev

# Get a list a preinstalled apt packages
RUN mkdir /src && \
    chown 1000:1000 /src && \
    dpkg-query -W -f='${binary:Package}=${Version}\n' > /src/pre_installed.txt && \
    echo "This image distributes binaries of copyleft licensed software. Please find the corresponding source code in our source-code distributing images (append -src to the image tags; e.g. syslifters/sysreptor:2024.58-src)." > /src/SOURCES.txt

# Install system dependencies required by weasyprint and chromium
# Install ghostscript from debian testing
RUN echo 'Types: deb\nURIs: http://deb.debian.org/debian\nSuites: trixie\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg' > /etc/apt/sources.list.d/testing.sources \
    && echo 'APT::Default-Release "stable";' > /etc/apt/apt.conf.d/default-release \
    && apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        curl \
        fontconfig \
        fonts-noto \
        fonts-noto-mono \
        fonts-noto-ui-core \
        fonts-noto-color-emoji \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        gpg \
        gpg-agent \
        libharfbuzz-subset0 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        unzip \
        wget \
        postgresql-client \
    && apt-get -t testing install -y --no-install-recommends ghostscript \
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
RUN pip install --no-cache poetry==1.8.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-cache --no-interaction --no-root

# Unprivileged user
RUN useradd --uid=1000 --create-home --shell=/bin/bash user \
    && mkdir -p /data /app/api && chown user:user /data /app/api
# Change owner and permissions to allow adding custom CA certificates
RUN chown 0:1000 /etc/ssl/certs/ && \
    chown 0:1000 /usr/local/share/ca-certificates/ && \
    chmod g+w /etc/ssl/certs/ && \
    chmod g+w /usr/local/share/ca-certificates/
USER 1000
VOLUME [ "/data" ]


# Configure application
ARG VERSION=dev
ENV VERSION=dev \
    DEBUG=off \
    MEDIA_ROOT=/data/ \
    SERVER_WORKERS=4 \
    PDF_RENDER_SCRIPT_PATH=/app/packages/rendering/dist/bundle.js \
    PLUGIN_DIRS=/app/plugins/

# Start server
EXPOSE 8000
CMD ["/bin/bash", "/app/api/start.sh"]



FROM --platform=$BUILDPLATFORM api-dev AS api-prebuilt

# Copy source code (including pre-build static files)
COPY --chown=user:user api/src /app/api/
COPY --chown=user:user rendering/dist /app/packages/rendering/dist/



FROM --platform=$BUILDPLATFORM api-dev AS api-test
# Copy source code
COPY --chown=user:user api/src /app/api/
COPY --chown=user:user plugins /app/plugins/
RUN mkdir -p /app/api/sysreptor_plugins/ && chmod 777 /app/api/sysreptor_plugins/

# Copy generated template rendering script
COPY --from=rendering --chown=user:user /app/packages/rendering/dist /app/packages/rendering/dist/


FROM --platform=$BUILDPLATFORM api-test AS api-statics
# Generate static frontend files
# Post-process django files (for admin, API browser) and post-process them (e.g. add unique file hash)
# Do not post-process nuxt files, because they already have hash names (and django failes to post-process them)
RUN python3 manage.py collectstatic --no-input --clear
COPY --from=frontend /app/packages/frontend/dist/index.html /app/packages/frontend/dist/static/ /app/api/frontend/static/
COPY --from=plugin-builder --chown=user:user /app/plugins/ /app/plugins/
RUN mv /app/api/frontend/static/index.html /app/api/frontend/index.html \
    && ENABLED_PLUGINS='*' python3 manage.py collectstatic --no-input --no-post-process


FROM api-test AS api
COPY --from=api-statics /app/api/frontend/index.html /app/api/frontend/index.html
COPY --from=api-statics /app/api/static/ /app/api/static/
COPY --from=api-statics /app/plugins/ /app/plugins/
USER 0
COPY --chown=1000:1000 api/generate_notice.sh api/download_sources.sh api/start.sh api/NOTICE /app/api/
RUN /bin/bash /app/api/generate_notice.sh
# Copy of changelog should be one of the last things to use cache for prod releases
COPY LICENSE CHANGELOG.md /app/
ARG VERSION=dev
ENV VERSION=${VERSION}
USER 1000


# These stages are only used in CI
FROM ${TESTED_API_IMAGE} AS api-prod
ARG VERSION
ENV VERSION=${VERSION}
COPY CHANGELOG.md /app/

FROM ${PROD_API_IMAGE} AS api-src
USER 0
RUN dpkg-query -W -f='${binary:Package}=${Version}\n' > /src/post_installed.txt \
    && bash /app/api/download_sources.sh
USER 1000



# Default stage
FROM api
