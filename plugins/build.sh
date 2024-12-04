#!/bin/bash
set -e  # exit on error

action="${1:-build}"
if [ "$action" != "build" ] && [ "$action" != "dev" ]; then
  echo "Usage: $0 [build|dev]"
  exit 1
fi


function build_plugin() {
  plugin="$1"
  action="$2"

  echo "$plugin: Build started"
  cd "$plugin"
  if [ -f "build.sh" ]; then
    echo "$plugin: Running build.sh $action"
    ./build.sh "$action"
  elif [ -d "frontend" ] && [ -f "frontend/package.json" ] && cat "frontend/package.json" | jq -e '.scripts.generate' > /dev/null; then
    echo "$plugin: Generating frontend"
    cd frontend
    npm install
    if [ "$action" == "dev" ]; then
      while : ; do
        echo "$plugin: Generating frontend"
        npm run generate || true
        echo "$plugin: Finished generating frontend"
        echo "$plugin: Watching for changes"
        inotifywait --recursive --event=create --event=delete --event=modify --event=move --exclude='^(.nuxt|.output|dist|node_modules|NOTICE)(/.*)?' ./ || break
        echo "$plugin: Changes detected"
      done
      exit 0
    else
      npm run generate
      rm -rf frontend
    fi
    cd ..
  else
    echo "$plugin: No build script found. Skipping"
  fi
  cd ..
  echo "$plugin: Build finished"
}


for plugin in *; do
  if [[ -d "$plugin" ]]; then
    if [ $action == "dev" ]; then
      # Start plugins in dev mode in parallel
      build_plugin "$plugin" "$action" &
    else 
      # Build plugins after each other
      build_plugin "$plugin" "$action"
    fi
  fi
done

if [ $action == "dev" ]; then
  wait
fi
