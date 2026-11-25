#!/bin/bash

set -e

CYBERCHEF_VERSION="v11.6.0"
CYBERCHEF_URL="https://github.com/gchq/CyberChef/releases/download/${CYBERCHEF_VERSION}/CyberChef_f464d62c7c943cda9749a765932a7548ba9bfb16.zip"

if [ ! -f "./static/cyberchef/CyberChef_${CYBERCHEF_VERSION}.html" ]; then
  echo "Downloading CyberChef"
  rm -rf static/cyberchef/*
  mkdir -p static/cyberchef
  curl -L "${CYBERCHEF_URL}" -o cyberchef.zip
  unzip cyberchef.zip -d static/cyberchef
  rm cyberchef.zip
else
  echo "CyberChef already exists. Skipping download."
fi
