# Security Considerations

## Template Injection
SysReptor uses server-side rendering for generating PDF reports. 
This allows template injection attackers.

This is intentional.

The template injection is sandboxed in a dedicated Chromium process. 
Chromium is running in offline mode. It has no possibility to connect to remote locations. 
It requires an exploit in the Chromium browser to get access to the container.

:octicons-cloud-24: Cloud · The Chromium process in our cloud is isolated in a dedicated Kubernetes pod. It receives rendering jobs via RabbitMQ, completes its rendering process and shuts down. An attacker breaking out of the Chromium process could prevent it from shutting down until a defined timeout. However, it would **not** be able to receive further rendering jobs.

:octicons-server-24: Self-Hosted · The Chromium process in self-hosted environments runs in an isolated process in the web application's docker container by default. An attacker breaking out of the Chromium process can also compromise the web application. However, it is possible to outsource the rendering process into a dedicated docker container. This requires two additional docker containers: Chromium and RabbitMQ. However, the Chromium process will be able to receive further rendering jobs (in contrast to the cloud setup).  
For resource reasons, we do not use this setup in the standard installation. 


## Denial of Service (DoS)
PDF rendering is a long-running and resource intensive process.
Especially WeasyPrint can sometimes be slow when rendering long and complex reports. 

Attackers can inject long-running instructions (via Vue, HTML or CSS) in templates. This might cause DoS of the rendering process.  
A timeout cancels the Vue template rendering process as soon as rendering time reaches a certain threshold.

DoS prevention is currently not implemented for WeasyPrint.
For now, we accept the risk of DoS in WeasyPrint, since we do not want to prevent rendering long and complex reports which might take some time and system resources.

This behavior might change in the future.

## Server-Side Request Forgery Prevention
All Requests to external systems from within the rendering workflow are blocked.
This prevents data exfiltration to external systems if attackers inject templates or if there are vulnerabilities in third-party JS libraries.

This is ensured by two measures:

1. The headless Chromium instances uses the offline mode. This simulates that the browser is offline and blocks all outgoing requests.
2. For WeasyPrint, we use a custom URL fetcher. This prevents requests to external systems. 
   It allows `data:`-URLs and access to files uploaded to SysReptor (designer assets, images) only.
   No HTTP requests are involved when including these resources (neither to localhost), 
   but a custom handler that returns the resources as data following the 
   [WeasyPrint security recommendations](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#security){ target=_blank }.


<div class="grid cards" style="margin: 4em;" markdown>
-   :material-shield-alert:{ .lg .middle } __Report a security issue__

    ---

    Discovered a security vulnerability?  
    Report it responsibly through our vulnerability disclosure process.

    [:octicons-arrow-right-24: Disclose responsibly](https://github.com/Syslifters/sysreptor/security){ target="_blank"}
</div>