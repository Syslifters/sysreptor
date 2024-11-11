#!/bin/sh
action="${1:-build}"

cd frontend
npm install

if [ "$action" = "dev" ]; then
  npm run build-watch
else
    npm run build
fi
