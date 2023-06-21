# Changelog

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
