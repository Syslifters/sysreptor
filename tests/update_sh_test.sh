#!/usr/bin/env bash
# After a failed container start, the next update.sh run must not report the
# release as installed: it checks that sysreptor-app runs the configured image.
set -eu

root=$(cd -- "$(dirname "$0")/.." && pwd)
work=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$work"' EXIT

if ! date -Iseconds >/dev/null 2>&1; then
    for d in /opt/homebrew/opt/coreutils/libexec/gnubin /usr/local/opt/coreutils/libexec/gnubin; do
        if [ -x "$d/date" ]; then PATH="$d:$PATH"; break; fi
    done
fi
if ! sed --version >/dev/null 2>&1; then
    for d in /opt/homebrew/opt/gnu-sed/libexec/gnubin /usr/local/opt/gnu-sed/libexec/gnubin; do
        if [ -x "$d/sed" ]; then PATH="$d:$PATH"; break; fi
    done
fi
date -Iseconds >/dev/null
sed --version >/dev/null

bin=$work/bin
mkdir -p "$bin"
cat > "$bin/curl" << 'EOF'
#!/bin/sh
out=""
while [ $# -gt 0 ]; do
    case "$1" in
        --output) out=$2; shift 2 ;;
        http*)
            printf '%s\n' "$1" >> "$CURL_LOG"
            case "$1" in
                *latest.version*) printf '%s\n' "$STUB_VERSION" ;;
                *setup.tar.gz*) cp "$STUB_TARBALL" "$out" ;;
                *) exit 1 ;;
            esac
            shift
            ;;
        *) shift ;;
    esac
done
EOF
cat > "$bin/docker" << 'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "$DOCKER_LOG"
case "$1 $2" in
    "compose version") exit 0 ;;
    "compose up") exit "${COMPOSE_UP_RC:-0}" ;;
    "inspect --format")
        [ -n "${STUB_APP_STATE:-}" ] || exit 1
        printf '%s\n' "$STUB_APP_STATE"
        ;;
esac
exit 0
EOF
chmod +x "$bin/curl" "$bin/docker"

install=$work/sysreptor
mkdir -p "$install/deploy" "$work/src/release/deploy"
printf 'SYSREPTOR_VERSION=2026.80\n#\n' > "$install/deploy/.env"
printf '\n' > "$install/deploy/app.env"
printf 'name: sysreptor\n' > "$install/deploy/docker-compose.yml"
cp "$root/update.sh" "$install/update.sh"
printf 'SYSREPTOR_VERSION=2026.86\n' > "$work/src/release/deploy/.env"
printf '\n' > "$work/src/release/deploy/app.env"
cp "$root/update.sh" "$work/src/release/update.sh"
tar -C "$work/src" -czf "$work/setup.tar.gz" release

export PATH="$bin:$PATH"
export CURL_LOG=$work/curl.log DOCKER_LOG=$work/docker.log
export STUB_TARBALL=$work/setup.tar.gz STUB_VERSION=2026.86 COMPOSE_UP_RC=1
: > "$CURL_LOG"
: > "$DOCKER_LOG"
out=$work/out

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    cat "$out" >&2
    exit 1
}

rc=0
bash "$install/update.sh" >"$out" 2>&1 || rc=$?
if [ "$rc" -eq 0 ]; then fail "failed start exited 0"; fi
if grep -q 'Successfully updated.' "$out"; then fail "failed start printed success"; fi
if grep -q '^rmi ' "$DOCKER_LOG"; then fail "failed start removed images"; fi
grep -qx 'SYSREPTOR_VERSION=2026.86' "$install/deploy/.env" || fail "new version was not kept"

# Runs update.sh with the release already in deploy/.env. It must change nothing.
second_run() {
    : > "$CURL_LOG"
    : > "$DOCKER_LOG"
    export STUB_APP_STATE=$1
    rc=0
    bash "$install/update.sh" >"$out" 2>&1 || rc=$?
    if [ "$rc" -ne 0 ]; then fail "second run exited $rc"; fi
    if grep -q 'setup.tar.gz' "$CURL_LOG"; then fail "second run downloaded a tarball"; fi
    if grep -q '^compose up' "$DOCKER_LOG"; then fail "second run started containers"; fi
    if grep -q '^rmi ' "$DOCKER_LOG"; then fail "second run removed images"; fi
}

assert_not_running() {
    if grep -q 'already installed' "$out"; then fail "$1: reported the release as installed"; fi
    grep -q 'sysreptor-app is not running that image' "$out" || fail "$1: did not say so"
    grep -qF "cd \"$install/deploy\" && docker compose up -d" "$out" || fail "$1: did not print the command"
}

second_run ''
assert_not_running "no container"
second_run 'false syslifters/sysreptor:2026.86'
assert_not_running "stopped container"
second_run 'true syslifters/sysreptor:2026.80'
assert_not_running "old image still running"

second_run 'true syslifters/sysreptor:2026.86'
grep -q 'already installed' "$out" || fail "running release was not reported as installed"
