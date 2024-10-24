#!/bin/sh

if [ ! -d static/cyberchef ]; then
  echo "Downloading CyberChef"
  mkdir -p static/cyberchef
  curl https://github.com/gchq/CyberChef/releases/download/v10.19.2/CyberChef_v10.19.2.zip -o cyberchef.zip
  unzip cyberchef.zip -d static/cyberchef
  rm cyberchef.zip
else
  echo "CyberChef already exists. Skipping download."
fi
