#!/usr/bin/env bash

set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Any subsequent(*) commands which fail will cause the shell script to exit immediately

allow_only="MIT"
allow_only="$allow_only;MIT License"
allow_only="$allow_only;MIT-CMU"
allow_only="$allow_only;BSD"
allow_only="$allow_only;BSD License"
allow_only="$allow_only;BSD-3-Clause"
allow_only="$allow_only;BSD 3-Clause OR Apache-2.0"
allow_only="$allow_only;Apache Software License"
allow_only="$allow_only;Apache 2.0"
allow_only="$allow_only;Apache-2.0"
allow_only="$allow_only;Apache-2.0 OR BSD-3-Clause"
allow_only="$allow_only;Apache-2.0 AND CNRI-Python"
allow_only="$allow_only;LGPL-3.0-only"
allow_only="$allow_only;GNU Lesser General Public License v3 (LGPLv3)"
allow_only="$allow_only;GNU Lesser General Public License v2 or later (LGPLv2+)"
allow_only="$allow_only;Mozilla Public License 2.0 (MPL 2.0)"
allow_only="$allow_only;MPL-2.0"
allow_only="$allow_only;PSF-2.0"
allow_only="$allow_only;Zope Public License"
allow_only="$allow_only;MIT AND Python-2.0"

ignore=""
ignore="$ignore randomcolor"  # Has MIT license but py package listed as UNKNOWN
ignore="$ignore wrapt"  # BSD-2-Clause
ignore="$ignore tiktoken"  # MIT
ignore="$ignore ujson"  # BSD-3-Clause

pip-licenses --allow-only "$allow_only" --ignore-packages $ignore >/dev/null
