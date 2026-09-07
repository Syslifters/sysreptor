#!/usr/bin/env bash
set -e
cd -- "$(dirname "$0")"
./upgrade_postgres.sh 18 --no-input
