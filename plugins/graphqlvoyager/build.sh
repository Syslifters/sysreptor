#!/bin/sh

if [ ! -r static/index.html ]; then
  cd frontend
  npm install
  npm run build
else
  echo "GraphQL Voyager already exists. Skipping download."
fi
