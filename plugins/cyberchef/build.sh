#!/bin/bash

set -euo pipefail

CYBERCHEF_VERSION="v11.6.0"
CYBERCHEF_URL="https://github.com/gchq/CyberChef/releases/download/${CYBERCHEF_VERSION}/CyberChef_f464d62c7c943cda9749a765932a7548ba9bfb16.zip"
CYBERCHEF_HTML="./static/cyberchef/CyberChef_${CYBERCHEF_VERSION}.html"

if [ ! -f "${CYBERCHEF_HTML}" ]; then
  echo "Downloading CyberChef"
  rm -rf static/cyberchef/*
  mkdir -p static/cyberchef
  curl -L "${CYBERCHEF_URL}" -o cyberchef.zip
  unzip cyberchef.zip -d static/cyberchef
  rm cyberchef.zip
else
  echo "CyberChef already exists. Skipping download."
fi


echo "Injecting Content-Security-Policy into ${CYBERCHEF_HTML}"

script_hashes=""
while IFS= read -r body; do
  [ -z "${body}" ] && continue
  hex="$(printf '%s' "${body}" | sha256sum | cut -d' ' -f1)"
  digest="$(printf '%b' "$(printf '%s' "${hex}" | sed 's/../\\x&/g')" | base64 -w0)"
  script_hashes+=" 'sha256-${digest}'"
done < <(awk '
  {
    s = $0
    while (match(s, /<script[^>]*>/)) {
      tag = substr(s, RSTART, RLENGTH)
      rest = substr(s, RSTART + RLENGTH)
      if (match(rest, /<\/script>/)) {
        if (tag !~ /src[[:space:]]*=/ && RSTART > 1)
          print substr(rest, 1, RSTART - 1)
        s = substr(rest, RSTART + RLENGTH)
      } else break
    }
  }
' "${CYBERCHEF_HTML}")

CSP_DIRECTIVES=(
  "default-src 'none'"
  "script-src 'self' 'wasm-unsafe-eval'${script_hashes}"
  "style-src 'self' 'unsafe-inline'"
  "img-src 'self' data: blob:"
  "font-src 'self'"
  "worker-src 'self' blob:"
  "base-uri 'none'"
  "object-src 'none'"
  "connect-src 'none'"
  "frame-src 'none'"
  "form-action 'none'"
)
CSP_CONTENT="$(printf '%s; ' "${CSP_DIRECTIVES[@]}")"
CSP_META="<meta http-equiv=\"Content-Security-Policy\" content=\"${CSP_CONTENT% }\">"

tmp_html="${CYBERCHEF_HTML}.tmp"
sed -E \
  -e 's|<meta http-equiv="Content-Security-Policy" content="[^"]*">||g' \
  -e "s|<head>|<head>${CSP_META}|" \
  "${CYBERCHEF_HTML}" > "${tmp_html}"
mv -f "${tmp_html}" "${CYBERCHEF_HTML}"
