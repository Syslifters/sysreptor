# Security Concerns

The Designer uses server-side rendering for generating PDF reports. This allows template injection attacks and can lead to remote code execution (RCE).

This is intentional.

The template injection is sandboxed in a dedicated Chromium process in the main Docker container. Chromium is running in offline mode. It has no possibility to connect to remote locations. It requires an exploit in the Chromium browser to get access to the container and the application.

We still recommend to limit access to the Designer via the [User Permissions](/user-permissions) following the principle of least privilege. (Note: Limiting access to the designer via privileges is not yet possible but will be.)
