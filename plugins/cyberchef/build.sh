#!/bin/bash

set -e

CYBERCHEF_VERSION="v11.5.0"
CYBERCHEF_URL="https://github.com/gchq/CyberChef/releases/download/${CYBERCHEF_VERSION}/CyberChef_8cd426dd4f40f1423912d5fad91b578a86a65112.zip"

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
