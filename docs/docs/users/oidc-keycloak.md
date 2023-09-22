---
title: Keycloak OIDC Configuration
---

# Keycloak OIDC Configuration
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Configuration at your OIDC provider
1. Create new Keycloak client for authentication and generate `client_id` and a `client_secret`
2. Add the callback-url: https://`<your-installation>`/login/oidc/keycloak/callback
    * Add the hostname where your SysReptor installation can be accessed.

## Cloud Setup
:octicons-cloud-24: Cloud

You are lucky. Just send the values from the previous steps to us and we'll take care :smiling_face_with_3_hearts:

## Self-Hosted Setup
:octicons-server-24: Self-Hosted

Create your OIDC configuration for SysReptor...

```json
{
    "keycloak": {
        "label": "Keycloak",
        "client_id": "<client-id>",
        "client_secret": "<client-secret>",
        "server_metadata_url": "https://keycloak.example.com/auth/realms/dev/.well-known/openid-configuration",
        "client_kwargs": {
            "scope": "openid email",
            "code_challenge_method": "S256"
        },
        "reauth_supported": false
    }
}
```

...and add it to your `app.env`:

```env
OIDC_AUTHLIB_OAUTH_CLIENTS='"keycloak": {"label": "Keycloak",...''
```

## Limitations
SysReptor reauthenticates users before critical actions. It therefore requires users to enter their authentication details (e.g. password and second factor, if configured).

Your Keycloak installation might not support enforced reauthentication. Your can try to set `"reauth_supported": true`. If the "SUDO" functionality does not work, set to this value to `false`.

To enforce reauthentication, users can set a password for their local SysReptor user. This will enforce reauthentication with the local user's credentials.
