#!/usr/bin/env bash
# A failed container start must be retryable: the next update.sh run starts
# containers again instead of reporting that the release is already installed.
set -eu

root=$(cd -- "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
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
grep -qx 'PREVIOUS_SYSREPTOR_VERSION=2026.80' "$install/deploy/.update-incomplete" || fail "previous version was not recorded"

: > "$CURL_LOG"
: > "$DOCKER_LOG"
COMPOSE_UP_RC=0
rc=0
bash "$install/update.sh" >"$out" 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then fail "retry exited $rc"; fi
if grep -q 'already installed' "$out"; then fail "retry treated the release as installed"; fi
if grep -q 'setup.tar.gz' "$CURL_LOG"; then fail "retry downloaded a tarball"; fi
grep -qx 'compose up -d' "$DOCKER_LOG" || fail "retry did not start containers"
grep -qx 'rmi syslifters/sysreptor:2026.80' "$DOCKER_LOG" || fail "retry did not remove the previous image"
if [ -e "$install/deploy/.update-incomplete" ]; then fail "retry left the marker"; fi
grep -q 'Successfully updated.' "$out" || fail "retry did not succeed"
