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
CMD npm run test


FROM frontend-test AS frontend
RUN npm run build



FROM node:16-alpine AS rendering-dev

WORKDIR /app/packages/markdown/
COPY packages/markdown/package.json packages/markdown/package-lock.json /app/packages/markdown/
RUN npm install

WORKDIR /app/rendering
COPY rendering/package.json rendering/package-lock.json /app/rendering/
RUN npm install


FROM rendering-dev AS rendering
COPY rendering /app/rendering/
COPY packages/markdown/ /app/packages/markdown/
RUN npm run build




FROM python:3.10-alpine AS api-dev

# Install system dependencies required by weasyprint and chromium
RUN apk add --no-cache \
        glib-dev \
        pango \
        fontconfig \
        ttf-freefont \
        font-noto \
        terminus-font \
        icu-data-full \
        chromium \
        gcc \
        g++ \
        qpdf-dev \
        postgresql-client \
    && fc-cache -f

# Install python packages
ENV PYTHONUNBUFFERED=on \
    PYTHONDONTWRITEBYTECODE=on
COPY api/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Configure chromium
ENV PYPPETEER_HOME=/app/pyppeteer/ \
    PYPPETEER_EXECUTABLE=/usr/lib/chromium/chrome
RUN mkdir -p /app/pyppeteer/ && \
    chown -R 1000:1000 /app/pyppeteer/

WORKDIR /app/api/


FROM api-dev AS api-test
# Copy source code
COPY api/src /app/api
# Copy generated PDF rendering file
COPY --from=rendering /app/rendering/dist /app/rendering/
ENV PDF_RENDER_SCRIPT_PATH=/app/rendering/bundle.js
CMD python3 manage.py test



FROM api-test as api
# Generate static frontend files
COPY --from=frontend /app/frontend/dist/ /app/api/frontend/
RUN DEBUG=on python3 manage.py collectstatic --no-input \
    && python3 -m whitenoise.compress /app/api/frontend/ /app/api/static/
# Configure application
ENV DEBUG=off \
    MEDIA_ROOT=/data/ \
    SERVER_WORKERS=3 \
    SERVER_THREADS=4

RUN mkdir /data && chown 1000:1000 /data && chmod 777 /data
VOLUME [ "/data" ]


# Start server
USER 1000
EXPOSE 8000
CMD python3 manage.py migrate && \
    gunicorn --bind=:8000 --workers=${SERVER_WORKERS} --threads=${SERVER_THREADS} reportcreator_api.wsgi:application
