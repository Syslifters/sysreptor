# Security Considerations

## Template Injection
SysReptor uses server-side rendering for generating PDF reports. 
This allows template injection attackers.

This is intentional.

The template injection is sandboxed in a dedicated Chromium process in the main Docker container. 
Chromium is running in offline mode. It has no possibility to connect to remote locations. 
It requires an exploit in the Chromium browser to get access to the container and the application.

## Denial of Service
PDF rendering is a long-running and resource intensive process.
Especially WeasyPrint can sometimes be slow when rendering long and complex reports. 

Denial of Service is possible by injecting long-running JavaScript in the Vue template or by using long-running HTML and CSS in WeasyPrint.

The Vue template rendering process is aborted if it takes longer than a certain time.

Currently, no DoS prevention is implemented for WeasyPrint.
For now we accept the risk of DoS in WeasyPrint, since we do not want to prevent rendering long and complex reports which might take some time and system resources.
This behavior might change in the future.

## Server-Side Request Forgery Prevention
All Requests to external systems from within the rendering workflow are blocked.
This prevents data exfiltration to external systems if attackers inject templates or if there are vulnerabilities in third-party JS libraries.

This is ensured by two measures:

* The headless Chromium instances uses the offline mode. This simulates that the browser is offline and blocks all requests.
* For WeasyPrint, a custom URL fetcher is used that prevents requests to external systems. 
  It allows `data:`-URLs and access to files uploaded to SysReptor (designer assets, images) only.
  No HTTP requests are involved when including this resources (neither to localhost), 
  but a custom handler that returns the resources as data following the [WeasyPrint security recommendations](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#security){ target=_blank }.



