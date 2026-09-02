#!/bin/bash

set -e

CYBERCHEF_VERSION="v11.4.0"
CYBERCHEF_URL="https://github.com/gchq/CyberChef/releases/download/${CYBERCHEF_VERSION}/CyberChef_49d1a5634a67a3b806c6db0fdca7dcecb41a776c.zip"

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
