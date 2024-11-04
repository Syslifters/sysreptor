---
title: Generic OIDC Configuration
---

# Generic OIDC Configuration
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Configuration at your OIDC provider
1. Create a `client_id` and a `client_secret` in your OIDC provider
2. Add the callback-url: https://`<your-installation>`/login/oidc/`<your-provider-name>`/callback
    * Add the hostname where your SysReptor installation can be accessed.
    * Choose a custom provider name (e. g. `keycloak`)

## Cloud Setup
:octicons-cloud-24: Cloud

You are lucky. Just send the values from the previous steps to us and we'll take care :smiling_face_with_3_hearts:

## Self-Hosted Setup
:octicons-server-24: Self-Hosted

Create your OIDC configuration for SysReptor...

```json
{
    "<your provider name>": {
        "label": "<human readable provider name>",
        "client_id": "<your client_id>",
        "client_secret": "<your_client_secret>",
        "server_metadata_url": "<link to OIDC provider's openid-configuration>",
        "client_kwargs": {
            "scope": "openid email",
            "code_challenge_method": "S256"
        },
        "reauth_supported": false
    }
}

```

```env
OIDC_AUTHLIB_OAUTH_CLIENTS='{"<your provider name>": {"label": "<human readable provider name>",...}}'
```

## Limitations
SysReptor reauthenticates users before critical actions. It therefore requires users to enter their authentication details (e.g. password and second factor, if configured).

Your OIDC provider might not support enforced reauthentication. Your can try to set `"reauth_supported": true`. If the "SUDO" functionality does not work, set to this value to `false`.

To enforce reauthentication, users can set a password for their local SysReptor user. This will enforce reauthentication with the local user's credentials.
