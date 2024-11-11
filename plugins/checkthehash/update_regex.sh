#!/bin/bash
# Fetches the latest prototypes.json (hash list) and convertes it into js readable format using docker.
cd jsregex
curl https://raw.githubusercontent.com/noraj/haiti/refs/heads/master/data/prototypes.json -o prototypes.json
docker build . -t jsregex 
docker container run jsregex > ../frontend/data/converted-prototypes.json