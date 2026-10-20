#!/usr/bin/env bash

set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_SRC="${SCRIPT_DIR}/src"

DEV=0
RUN_MIGRATE=0
START_SERVER=0
START_WORKER=0
WORKER_EXPLICIT=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --dev                     Development mode (reload on code changes)
  --server/--no-server      Start web server
  --worker/--no-worker      Start taskiq worker
  --migrate/--no-migrate    Run database migrations
  -h, --help                Show this help

Default: start server and worker (worker requires redis).
EOF
}

OPTS="$(getopt -o h --long dev,server,no-server,worker,no-worker,migrate,no-migrate,help -n "$(basename "$0")" -- "$@")" || {
    usage >&2
    exit 1
}
eval set -- "${OPTS}"
while true; do
    case "$1" in
        --dev) DEV=1 ;;
        --server) START_SERVER=1 ;;
        --no-server) START_SERVER=0 ;;
        --worker) START_WORKER=1; WORKER_EXPLICIT=1 ;;
        --no-worker) START_WORKER=0 ;;
        --migrate) RUN_MIGRATE=1 ;;
        --no-migrate) RUN_MIGRATE=0 ;;
        -h|--help) usage; exit 0 ;;
        --) shift; break ;;
        *) echo "Unexpected option: $1" >&2; exit 1 ;;
    esac
    shift
done

if [[ $# -gt 0 ]]; then
    echo "Unexpected arguments: $*" >&2
    usage >&2
    exit 1
fi

# Default: start both
if [[ "${START_SERVER}" -eq 0 && "${START_WORKER}" -eq 0 && "${RUN_MIGRATE}" -eq 0 ]]; then
    RUN_MIGRATE=1
    START_SERVER=1
    START_WORKER=1
fi

WAIT_PIDS=()
STOPPING=0

shutdown() {
    if [[ "${STOPPING}" -eq 1 ]]; then
        return 0
    fi
    STOPPING=1
    if [[ "${#WAIT_PIDS[@]}" -gt 0 ]]; then
        kill -TERM "${WAIT_PIDS[@]}" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
}
trap shutdown TERM INT EXIT

# Run DB migrations
if [[ "${RUN_MIGRATE}" -eq 1 ]]; then
    python3 "${API_SRC}/manage.py" migrate
fi

if [[ "${START_SERVER}" -eq 1 ]]; then
    if [[ "${DEV}" -eq 1 ]]; then
        python3 -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 -m uvicorn \
            --reload \
            --reload-include '*.html' \
            --host 0.0.0.0 \
            --port 8000 \
            sysreptor.conf.asgi:application &
    else
        gunicorn --bind=:8000 \
                 --worker-class=uvicorn_worker.UvicornWorker \
                 --workers="${SERVER_WORKERS:-4}" \
                 --max-requests=1000 \
                 --max-requests-jitter=100 \
                 --graceful-timeout="${SERVER_WORKER_RESTART_TIMEOUT:-3600}" \
                 --timeout="${SERVER_WORKER_RESTART_TIMEOUT:-3600}" \
                 sysreptor.conf.asgi:application &
    fi
    WAIT_PIDS+=($!)
fi

if [[ "${START_WORKER}" -eq 1 ]]; then
    if [[ -z "${REDIS_URL:-}" && ( -z "${REDIS_CONNECTION_CONFIG:-}" || "${REDIS_CONNECTION_CONFIG}" == "null" ) ]]; then
        echo "Warning: Redis not configured; skipping Taskiq worker" >&2
        if [[ "${WORKER_EXPLICIT}" -eq 1 ]]; then
            echo "Redis is required to start the worker (set REDIS_URL)" >&2
            exit 1
        fi
    else
        if [[ "${DEV}" -eq 1 ]]; then
            WORKER_ARGS=(
                --workers=1
                --reload
            )
        else
            WORKER_ARGS=(
                --workers="${TASK_WORKERS:-2}"
                --max-async-tasks=1000
                --max-tasks-per-child=1000
                --wait-tasks-timeout="${SERVER_WORKER_RESTART_TIMEOUT:-3600}"
            )
        fi
        taskiq worker \
            sysreptor.conf.taskiq_worker:broker \
            --no-configure-logging \
            "${WORKER_ARGS[@]}" &
        WAIT_PIDS+=($!)
    fi
fi

if [[ "${#WAIT_PIDS[@]}" -eq 0 ]]; then
    echo "Nothing to start" >&2
    exit 1
fi
wait -n "${WAIT_PIDS[@]}"
