# Changelog

## Upcoming
* Suggest previously used tags in filters, projects, designs and templates
* Plugin `scanimport`: Prevent errors on incompatible finding field types


## v2025.81 - 2025-09-24
* Fix error when opening design notes page


## v2025.80 - 2025-09-24
* Add excalidraw notes to SysReptor core
* Deprecate `excalidraw` plugin
* Case sensitive todo marker parsing
* Allow importing notes to design default note structure
* Allow using a custom PostgreSQL schema via `DATABASE_SCHEMA`
* Auto-complete usernames in comments
* Update HTB CBBH design to HTB CWES
* Fix CSP errors related to `strict-dynamic` directive


## v2025.74 - 2025-09-10
* Plugin `scanimport`: Import scan results from various tools
* Fix date field empty value not saved as null
* Fix outbound connection established during PDF rendering
* Markdown editor: fix pasted images not inserted correctly in some cases
* Markdown editor: do not format as markdown when pasting into code blocks
* Update executive summary section in HTB CBBH design
* Require email address for user creation
* Require a different password when changing passwords
* Improve setting proxy variables
* Use nonce instead of hash for CSP `script-src`


## v2025.69 - 2025-08-13
* Replace deprecated bitnami redis docker image with official redis image
* Plugin `markdownexport`: Export reports as Markdown documents in ZIP format
* Fix out of memory bug in `StreamingHttpResponseAsync`
* Fix crypto stream errors logged on cleanup
* Fix `run_in_background` after `asgiref` update
* Fix custom CA certificates not loaded for commands
* Log backup started and finished times
* Restore backup: bulk insert DB objects
* PDF viewer: add stricter postMessage validation to prevent errors on unexpected messages
* Allow collapsing plugin menu


## v2025.64 - 2025-07-30
* Plugin `excalidraw`: Integrate Excalidraw in SysReptor
* Allow customizing finding/section statuses (https://docs.sysreptor.com/setup/configuration/#custom-statuses)
* Limit publicly accessible settings in API responses
* `restorebackup` command: add option to skip restoring files
* Improve markdown editor toolbar responsive layout on sidebar width change
* PDF viewer: add PDF outline view
* PDF viewer: fix single-letter shortcuts applied when typing in searchbar input
* PDF viewer: fix message overlay covers footer
* Markdown editor: fix scroll sync to wrong position on HTML blocks starting with `<br>` tags
* Markdown editor: convert HTML (e.g. Excel tables, Word, etc.) to markdown on paste
* Markdown editor: add blockquote button toolbar
* Markdown editor: fix dropping files below last line


## v2025.56 - 2025-06-17
* Incremental parsing in markdown editor
* Add user setting to disable local login
* Provide parent CWEs in PDF rendering
* Allow copying notes
* Bulk delete and bulk export notes
* UI: allow multi-select in notes tree
* UI: fix UI not updated after finish and reactivate project
* UI: fix version history sidebar behind comment sidebar
* UI: fix search text reset on click outside of CreateFindingDialog
* PDF viewer: disable auto-linking


## v2025.50 - 2025-05-28
* Sync scroll in markdown editor and preview
* Pin ghostscript version to fix bugs in pdf compression
* Prevent PDF rendering Vue warning about tr children of table tags
* PDF viewer: Allow navigation via arrow keys
* UI: Add a button to expand collapsed menus
* UI: Fix sections not sorted in sidebar
* UI: Add shortcut indicator to save comments


## v2025.43 - 2025-05-07
* Notifications about project updates (https://docs.sysreptor.com/users/notifications/)
* Rework and update PDF viewer
* Allow spellchecking all supported languages instead of only `PREFERRED_LANGUAGES`
* UI: do not hide assignee field on small screens
* UI: Findings/sections/notes editor performance improvements
* Plugin `projectnumber`: do not overwrite existing project tags


## v2025.37 - 2025-04-17
* Allow sending emails (https://docs.sysreptor.com/setup/configuration/#emails)
* Add forgot password functionality (https://docs.sysreptor.com/setup/configuration/#local-user-authentication)
* Make user emails unique
* Fix number field not accepting decimal numbers
* Fix importing backups without stored configurations
* Fix mermaid rendering not finished race condition in PDFs
* UI: Template editor performance improvements
* Improve default checkbox styles in PDFs


## v2025.29 - 2025-03-26
* Allow grouping of findings (https://docs.sysreptor.com/designer/findings/#finding-groups)
* SSO: Fix priority of `email` vs. `preferred_username`
* Restructure python modules
* Docs: Plugin development guide (https://docs.sysreptor.com/setup/plugins/)


## v2025.25 - 2025-03-19
* Plugin `renderfindings`: allow rendering finished projects
* Plugin `webhooks`: webhooks on update
* UI: Add sync indicator
* UI: Refine publish project page
* API: allow setting `text_range` when creating comments via API
* Fix duplicate entries in template search results
* Allow searching for member usernames in project list
* Enable toggle comment shortcut in HTML/CSS editor
* SSO: Use `preferred_username` as user identifier in addition to `email`


## v2025.20 - 2025-03-05
* Fix corrupt backup.zip because output file is not closed in backup CLI command
* Add log message when backup is finished
* Increase gunicorn worker restart timeout to prevent aborted backup requests
* Add command `createapitoken`
* Restrict system users: prevent access to projects, templates, designs
* Configure minium and maximum value for number fields
* Refactor application setting loading
* View and edit application settings in the web UI
* View and edit plugin settings in the web UI
* Prevent creating unresolvable empty comments
* UI: fix theme color in spellcheck tooltips
* UI: improve note tree sorting via drag-and-drop
* Plugin `renderfindings`: Add option to render findings to separate PDFs


## v2025.12 - 2025-01-27
* Do not automatically log in (e.g. via OIDC) after logout
* OIDC: use preferred_username as login_hint for re-authentication
* Accept username from env variable in createorupdateuser command
* Render markdown preview in web worker
* Show tooltips on list actions for missing permissions
* Project Design selection improvements: order by usage count
* Improvements of sharing notes and reports
* Configure user profile colors
* Find and replace in markdown fields
* Allow searching in findings and sections
* Plugin projectnumber: Fix different projectnumber generated for tag and field
* Command `importdemodata`: Handle `--add-member` option unset
* Add option to disable archiving for project members
* Fix setting loading for `DEFAULT_STORAGE`


## v2025.4 - 2025-01-14
* Plugin projectnumber: Add manage.py command to reset projectnumber
* Add plugin: renderfindings - Render single finding to PDF
* Update and optimize designs: demo, HTB and OffSec designs
* Add design for HTB CAPE certification
* Warn about relative URLs in PDFs during rendering
* Add button to generate random password to password fields
* Shared notes: Default to markdown preview mode for readonly shares
* Shared notes: Autofocus root note
* Fix DB connection cleaned up in background tasks
* Increase DB connection pool size
* UI: Hide markdown toolbar in preview mode
* UI: Update UI to switch markdown editor view mode


## v2024.96 - 2024-12-04
* Plugin: webhooks at certain events
* Plugin: automatically assign project numbers
* Run periodic tasks in background
* Add user option to force password change on next login
* Fix finding.created not included in design preview data 
* Allow marking resolved comments as open
* UI: Create comments with Ctrl+Alt+M
* UI: Save comment texts with Ctrl+Enter
* UI: fix line break in logo text on Firefox


## v2024.91 - 2024-11-20
* Introduce a plugin system (experimental)
* Add plugins: CyberChef, GraphQL Voyager, Hash Identifier
* Disable static file compression
* Allow to cancel PDF rendering requests
* Enforce PDF rendering timeout in self-hosted installations (default: 5 min)
* Show PDF render timing information
* Always remove PDF metadata
* Add button to download preview PDF
* Fix error while updating user fields via REST API
* Update HTB designs to improve table rendering performance


## v2024.81 - 2024-10-25
* Fix mermaid diagram labels not rendered
* Disable CSP trusted types enforcement because of incompatibilities
* Autofocus TOTP input field in login form


## v2024.79 - 2024-10-15
* Add more granular file storage settings
* Add trusted types configuration to Content Security Policy
* Markdown editor: Add toolbar button to reference findings
* Markdown editor: Show markdown snippet in markdown image preview dialogs
* Bugfixes in note sharing
* Fix race condition when creating comments for text selection
* Reset DB sequences on restore backup to prevent ID conflicts


## v2024.74 - 2024-09-24
* Public note sharing
* Add permission Project Admin
* Update ghostscript to fix multiple bugs in pdf post-processing


## v2024.70 - 2024-09-04
* Set custom database credentials in languagetool container
* Fix bug when using custom CA


## v2024.69 - 2024-08-30
* Fix install and update procedures
* Fix error importing designs without ordering fields
* Rename version history close button


## v2024.68 - 2024-08-29 (pre-release)
* Rework field definition data format. Warning: breaking API changes
* Allow custom order of object field properties
* Allow sorting combobox suggestions
* More settings for guest user permissions: GUEST_USERS_CAN_EDIT_PROJECTS, GUEST_USERS_CAN_SEE_ALL_USERS
* Improve error messages for decryption errors
* Fix user.is_active checkbox not reactive in edit user page
* Fix checkboxes not rendered as checked in PDF
* Provide prebuilt Docker images
* Fix chromium error while rendering PDFs


## v2024.63 - 2024-08-07
* Allow searching notes in frontend
* Retry redis commands on connection errors
* Fix mermaid init blocks not applied in PDF rendering
* Fix class paths of S3 storage backends
* Fix SPELLCHECK_URL not set in docker-compose
* Fix permission denied when user is superuser and guest


## v2024.61 - 2024-07-31
* Fix error in update.sh script for languagetool and caddy updates
* Fix prebuilt frontend JS files not used in docker image


## v2024.60 - 2024-07-31
* Rework install.sh
* Set restart policy for redis docker container
* Add setting to disable websockets and always use HTTP for collaborative editing
* Fix error while sorting finding templates by created/updated date
* Fix create template from finding changes not saved


## v2024.58 - 2024-07-10
* Fix API token authentication in community edition


## v2024.57 - 2024-07-10
* Fix set assignee in notes, findings and sections
* Fix error when setting note checkboxes
* Suggest values used in other findings in combobx fields
* Navigate through images in enlarged markdown image preview dialog


## v2024.55 - 2024-07-04
* Allow commenting finding and section fields and markdown text
* Create backups via web interface
* Show backup history in web interface
* Store last usage date for API tokens
* Allow duplicating findings
* Compress PDFs to reduce file sizes
* Use redis as channels layer instead of postgres for collaborative editing
* Fix template pagination error for templates without CVSS score
* Fix multiple bugs in collaborative editing over websockets
* UI: Add button to copy confirm text in delete confirm dialogs
* UI: Fix create finding dialog searchbar cleared on click outside
* UI: Sticky toolbar in markdown editor


## v2024.49 - 2024-06-18
* Enable fontconfig cache in docker container
* Respect verbosity option in `backup` and `restorebackup` commands
* Immediately create new templates in API to allow image uploads on first editing
* Fix importing of non-empty note assignees
* Collaborative editing: Sync pending changes on reconnect
* Fix collaborative editing updates applied out-of-order because of MDE update throttling
* Set `Secure` flag for cookies when setting `SECURE_SSL_REDIRECT=on`


## v2024.43 - 2024-05-27
* Add sorting options to projects, templates, designs and users lists
* Collaborative editing in project history diff views
* Project history diff views: add revert changes button to markdown editor
* Send update_text events with text diff when updating text fields via API instead of overwriting the whole text
* Fix MDE preview layout break on zoom out
* Throttle MDE update events to prevent browser from hanging
* Fix elastic APM tracing middleware always enabled


## v2024.40 - 2024-05-15
* Collaborative editing in project findings and sections
* Collaborative editing: update notes list when import new notes
* Collaborative editing: HTTP fallback if no WebSocket connection can be established
* Fix slot data items `.length` property undefined `<list-of-figures>`, `<list-of-tables>` and `<table-of-contents>` components
* Fix CSRF vulnerability for WebSocket connections
* Introduce `ALLOWED_HOSTS` setting for request host and origin validation


## v2024.30 - 2024-04-17
* Update dependencies to fix request-smuggling vulnerabilities in gunicorn (CVE-2024-1135)


## v2024.28 - 2024-04-10
* Collaborative editing in notes
* Show cursor position and selection of other users for collaborative editing in notes
* Remember "Encrypt PDF" setting in browser's local storage
* Fix force change design API request not sent
* Add Content Security Policy directive form-action
* Strengthen Content Security Policy: remove script-src unsafe-inline
* Fix API token expiring today shown as expired in UI
* Fix squished buttons on publishing project page
* Markdown editor: Improve vue template variable handling
* Markdown editor: Allow escaping curly braces


## v2024.20 - 2024-04-02
* Fix PDF rendering hanging on headless chromium startup


## v2024.19 - 2024-03-05
* Allow configuring the PDF rendering timeout (applies only when a separate worker is used)
* Add filename in markdown editor for uploaded files
* Move cursor after uploaded file/image in markdown editor
* Prevent cutting off spellcheck error underlines in string fields
* Add more language variants for spellcheck
* Allow duplicating finding templates
* Fix error in periodic task for automatic project archiving


## v2024.16 - 2024-02-22
* Add component for cover pages in PDF designer layout editor
* Reference `<figure>` tag instead of `<figcaption>` in `<ref />` component to jump to start of figure
* Enable multi-selection in markdown editor
* Fix CWE field formatting for PDF rendering
* Add HackTheBox CWEE design


## v2024.13 - 2024-02-14
* Add CWE field type
* Break text in tables to prevent tables overflowing page in base styles
* Sync updated field default values to preview data fields
* Automatically close brackets and enclose selected text with brackets in markdown editor
* UI: Add hint how to add custom tags
* UI: Add buttons for task list and footnote to markdown editor toolbar
* Fix text selection in markdown preview focus changed to editor
* Fix object field properties not always sorted
* Fix newline not inserted at empty last line of markdown editor in Firefox
* Fix ID form field loses focus while writing in report field page


## v2024.10 - 2024-01-25
* Define initial note structure for projects in designs
* Allow exporting and importing notes
* Include project name in default PDF filename on puglish project page
* Fix chapter number always prepended to title in `<ref />` component
* Fix attributes not inherited to nested input fields
* Fix readonly code editor in PDF designer still writable


## v2024.8 - 2024-01-23
* Diff-view for version history
* Set form fields readonly instead of disabled
* Update build system of Vue PDF rendering script from webpack to vite
* Improve template field overview UI
* Fix error while editing ID of nested field of report section in designer
* Add demo data archives as TOML files to repository
* Fix resizing PDF viewer loses mouse focus in Firefox
* Add raptor mascot images as to empty pages
* Increase contrast of nested form fields
* Show more detailed error messages in frontend


## v2024.3 - 2024-01-09
* Fix PDF viewer crash in Chrome with Bitwarden browser extension


## v2024.1 - 2024-01-08
* Design and UI rework
* Dark mode
* Disable buttons and menu entries when user does not have permissions
* Fix save error for user fields
* Ensure custom fonts are loaded before rendering charts and diagrams
* Remove status emoji of notes
* Separate settings for spellcheck and markdown preview mode in projects, notes, templates, designs
* Click to enlarge images in markdown preview
* Consolidated project history
* Fallback to severity if CVSS is undefined in template list
* Add status and tags to designs


## v2023.145 - 2023-12-11
* Add support for mermaid diagrams in markdown
* Fix arrow movement in fields inside lists to switch list item
* Fix guest restriction configuration loading
* Allow configuring regex patterns for list items
* Add scheme to predefined URL regex
* Fix list items not updated in design preview data form
* Prevent page offset jumping when switching markdown editor mode
* Allow sorting items of list fields in reports
* Support text input in date fields


## v2023.142 - 2023-11-21
* CVSS 4.0 support
* Allow requiring a specific CVSS version in CVSS fields
* Allow accessing designer assets in Chromium during PDF rendering
* Support validating string fields with RegEx patterns
* Add an API endpoint to retrieve project data with markdown fields rendered to HTML
* Do not send unreferenced images to PDF rendering task to reduce memory usage
* Do not export images that are not referenced in exported data
* Prevent migration errors caused by DB queries in license check
* Fix spellcheck returning no results for language=auto
* Fix markdown preview flappy scroll on typing in markdown editor when images are included
* Fix OIDC login for re-authentication not working
* Fix focus lost while editing object field property IDs in designer 


## v2023.136 - 2023-10-30
* Update frontend tech stack to Vue3, Nuxt3, Vuetify3, Typescript
* Update weasyprint to v60
* Increase read timeout in example nginx config
* Prevent duplicate PDF warnings
* Prevent disabling current user
* Allow removing current user from project members
* Prevent footnotes from moving to next page by default in base.css styles
* Default to manual sorting if not finding ordering fields are defined in design
* Fix spellcheck errors when using per-user dictinaries


## v2023.128 - 2023-09-21
* Version history for projects, designs and templates
* UI: Decrease font size of note assignee in list to match finding/section assignee style
* UI: Autofocus note and finding title after create
* UI: More prominent translate template field button
* UI: Include more details on license errors


## v2023.122 - 2023-09-07
* Fix template appears multiple times in search result list when multiple languages match
* Assign notes to users
* Install more Noto Sans fonts to support more languages
* Ignore whitespaces in delete confirm dialogs
* Use proxy config of host in docker-compose containers


## v2023.119 - 2023-08-23
* UI: sticky header and searchbar in list views
* UI: increase file drop area for importing projects, designs and templates
* Configure finding sort order in design
* Allow manual ordering of findings by overriding the default sort order
* Allow ordering of enum choices in design field definition
* Search in all fields for template search
* Add shortcut for creating new findings and notes (Ctrl+J)


## v2023.114 - 2023-08-09
* Remove beta label and change versioning scheme
* Export notes as PDF
* Speed up unit tests for API
* Add CLI command to restore backups
* Sort users alphabetically in selection
* Clear user specific data from Vuex stores on logout
* Filter notifications in API when fetching instead of locally in instances
* Add datalabels plugin for Chart.js in designs
* Fix backward compatible import of templates with old format (format: templates/v1)
* Fix horizontal input field overflows in template editor
* Expose more CVSS information in designs (including CVSS version, base/temporal/environmental score, impact/exploitability subscores)
* Allow adding custom CA certificates to the docker containers during build 


## v0.110 - 2023-07-31
* Multilingual templates
* Support images in templates
* Support creating templates from findings
* UI: Move secondary toolbar actions to a dropdown menu
* UI: Sticky Add button in finding and note list sidebars
* Fix redirect after login for remoteuser default auth provider


## v0.102 - 2023-07-05
* Fix serialization of project check messages


## v0.101 - 2023-07-05
* Implement file upload in user notebook
* Optimize image loading in markdown preview
* Use Argon2 for hashing passwords instead of PBKDF2
* Authentication via API tokens
* Auto-generate OpenAPI schema


## v0.96 - 2023-06-22
* Fix username/password auth not available in login form of community edition


## v0.95 - 2023-06-21
* Store a reference to the original project/design when copying
* Add tags to projects
* UI: Add icons for tags/members/language in project and template list
* Add drag-and-drop PDF designer
* Support SSO via Remote-User HTTP header
* Allow disabling local authentication via username/password to force SSO
* Support configuring default authentication provider via setting DEFAULT_AUTH_PROVIDER
* Fix CSRF error during logout
* Support automatic archiving of finished projects via setting AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER
* Support automatic deletion of old archived projects via setting AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER
* Allow importing private designs
* Show warnings and info messages in designer error list
* Log invalid or unsupported CSS rules in PDF designer
* Include font files in repository


## v0.89 - 2023-06-06
* Update dependencies to fix vulnerabilities in python requests (CVE-2023-32681) and webpack (CVE-2023-28154)
* Prevent setting reference-type specific CSS classes to `<ref>` components with slot content
* Prevent buffering full `StreamingHttpResponse` causing high memory load
* Add fonts Roboto Flex, STIX Two Text and Arimo
* Remove non-variable fonts Roboto, Tinos, Lato and Courier Prime
* Configure fallback of common fonts to similar looking fonts (Arial, Helvetica, Times New Roman, Courier New, Verdana)


## v0.87 - 2023-05-24
* Provide (optional) base styles in designer via `@import "/assets/global/base.css";`
* Add `<ref>` component to designs to reference headings, figures, tables and findings
* Support writing markdown inside design HTML templates via `<markdown>` component
* Support markdown attrs for headings
* Allow `<u>` and `<pagebreak />` in markdown
* Provide lodash utility functions in design template
* The update script rebuilds Docker images every seven days to ensure dependencies are updated regularly
* Fix user type field formatting in design rendering
* Add settings for OIDC with Google


## v0.83 - 2023-05-12
* Fix parsing of nested markdown labels (link in footnote in image caption)
* On file not found during PDF rendering: add reference to finding/section in error message
* Add more languages
* Allow confiuring languages via setting PREFERRED_LANGUAGES
* Show current software version in license page
* Allow deleting users via UI
* Fix markdown code block alignment
* Update django to 4.2.1 (security release)


## v0.76 - 2023-05-02
* Release Community Edition
* Add license checks and enforce license limits
* Project archiving and encryption with 4-eye principle
* Improve list editing in markdown editor
* Add a refresh PDF button to the publish project page


## v0.19 - 2023-04-11
* Add private designs visible only to your user
* Support Postgres with PgBouncer in LanguageTool
* Allow storing files in S3 buckets
* Fix backup restore failing for notifications


## v0.18 - 2023-03-13
* Allow setting emojis as custom note icons
* Require re-authentication to enable admin permissions in user sessions
* Test and improve backup and restore logic
* Automatically cleanup unreferenced files and images
* Add words to spellcheck dictionary
* Allow removing and updating roles of imported project members
* Fix label not shown for number fields


## v0.17 - 2023-03-01
* Use variable Open Sans font to fix footnote-call rendering ("font-variant-position: super" not applied)


## v0.16 - 2023-02-23
* Personal and per-project notes
* Use asgi instead of wsgi to support async requests
* Async PDF rendering and spellcheck request
* Support Elastic APM for API and frontend monitoring
* Fetch and display notifications to users
* Add titles to pages in frontend


## v0.15 - 2023-02-06
* Support login via OpenID Connect
* Support offloading PDF rendering to a pool of worker instances
* Spellchecking and highlighting TODOs in string fields
* Make toolbar sticky on top of finding, section and template editor
* Separate scrollbars for side menu and main content
* Rework PDF Viewer


## v0.14 - 2023-01-03
* Data-at-rest encryption for files and sensitive DB data
* Use Session cookies instead of JWT tokens
* Support two factor authentication with FIDO2, TOTP and Backup Codes
* Add user role and permissions for system users
* Support encrypting backups


## v0.13 - 2022-12-16
* Add logo and favicon
* Add per-project user tags
* UI Improvement: create finding dialog: reset template search input after closing dialog, set search query as finding title for new empty findings
* UI Improvement: allow text selection in Markdown editor preview area


## v0.12 - 2022-12-05
* Provide some standard fonts in the docker container
* Customize designs per project
* Allow force changing designs of projects if the old and new design are incompatible
* Update Chromium to fix CVE-2022-4262 (high)


## v0.11 - 2022-11-25
* Compress images to reduce storage size and PDF size
* Manual highlighting of text in markdown code blocks
* Add review status to sections, findings and templates
* UI improvements: rework texts, add icons, more detailed error messages, group warnings by type in the publish page
* Fix rendering of lists of users containing imported project users


## Initial - 2022-11-16
* Begin of changelog
* Collaboratively write pentesting reports
* Render reports to PDF
* Customize report designs to your needs
* Finding Template library
* Export and import designs/templates/projects to share data
* Multi Language support: Engilsh and German
* Spell checking
* Edit locking
* Drag-and-drop image upload
* PDF encryption
* and many more features
