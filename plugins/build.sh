#!/bin/sh
set -e  # exit on error

for plugin in ./*; do
  if [[ -d "$plugin" ]]; then
    echo "Start building $plugin"

    cd "$plugin"
    if [ -f "build.sh" ]; then
      echo "Running build.sh"
      ./build.sh
    elif [ -d "frontend" ] && [ -f "frontend/package.json" ] && cat "frontend/package.json" | jq -e '.scripts.generate' > /dev/null; then
      echo "Generating frontend"
      cd frontend
      npm install
      npm run generate
      rm -rf frontend
      cd ..
    else
      echo "No build script found. Skipping"
    fi
    cd ..

    echo "Finished building $plugin"
  fi
done
