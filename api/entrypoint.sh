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

# Execute the command passed as arguments
exec "$@"
