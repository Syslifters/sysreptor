# How to build and deploy the docs manually
## Getting started

```
pip3 install -r requirements.txt

# Local deployment
cd docs
mkdocs serve

# Manually compiling report software list
python3 -c 'from hooks import *; generate_software_lists()'
```

## Build

```
# Build docs
cd docs/
python3 -c 'from hooks import *; generate_software_lists()'
mkdocs build
```

## Deploy

```
git clone https://github.com/Syslifters/sysreptor-docs.git ghpages
rm -rf ghpages/*
cp -r docs/sites/* ghpages/

# Stash history and deploy to GitHub
git add .
git commit -m "INIT"
git reset $(git commit-tree HEAD^{tree} -m "INIT")
git push --force
```
