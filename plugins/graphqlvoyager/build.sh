#!/bin/sh

if [ ! -d static/voyager ]; then
  mkdir static/voyager
  # Download sample introspection shema
  curl https://raw.githubusercontent.com/graphql-kit/graphql-voyager/refs/heads/main/demo/presets/swapi_introspection.json -o static/voyager/introspection.json
  # Adds Licences to NOTICE file
  npm run dependencies
  # Adds HTML, JS and CSS files to static/voyager
  npm run build
else
  echo "GraphQL Voyager already exists. Skipping download."
fi
