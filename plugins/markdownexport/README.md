# Markdown Export Plugin

Export SysReptor penetration testing reports as Markdown documents in a ZIP package. Designed for HackTheBox CWEE certification requirements.

## Installation

Add `markdownexport` to the `ENABLED_PLUGINS` variable in your `app.env` and restart your containers using `docker compose up -d` from the `deploy` directory.

```
ENABLED_PLUGINS="markdownexport"
```

The plugin will automatically add a "Markdown Export" button to the publish/download section of your projects.

## Usage

1. Open your project in SysReptor
2. Navigate to the publish page
3. Click the "Markdown Export" button to download your report as a ZIP

## Output Structure

The exported ZIP file contains:

```
report-export.zip
├── report.md          # Complete report in Markdown format
├── assets/            # Referenced images and screenshots
│   ├── image1.png
│   ├── screenshot2.jpg
│   └── ...
└── exploits/          # Exploit scripts and files (CWEE projects)
    ├── exploit.py
    ├── payload.sh
    └── ...
```
