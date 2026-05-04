---
title: Keycloak OIDC Configuration
---

# Keycloak OIDC Configuration
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Configuration at your OIDC provider
1. Create new Keycloak client for authentication and generate `client_id` and a `client_secret`
2. Add the callback-url: https://`<your-installation>`/login/oidc/keycloak/callback
    * Add the hostname where your SysReptor installation can be accessed.

## SysReptor Configuration

Create your OIDC configuration for SysReptor...

```json
{
    "keycloak": {
        "label": "Keycloak",
        "client_id": "<client-id>",
        "client_secret": "<client-secret>",
        "server_metadata_url": "https://keycloak.example.com/realms/dev/.well-known/openid-configuration",
        "client_kwargs": {
            "scope": "openid email",
            "code_challenge_method": "S256"
        },
        "reauth_supported": false,
        "user_identifier_claim": "email",
        "require_email_verified": false
    }
}
```

...and add it to your [application settings](/setup/configuration/#single-sign-on-sso) (`OIDC_AUTHLIB_OAUTH_CLIENTS`).

The OIDC client needs to be able to establish a network connection to Keycloak.
Make sure to not block outgoing traffic.

Other JSON fields, `user_identifier_claim`, and SSO limitations are covered in [Generic OIDC configuration](oidc-generic.md#sysreptor-configuration) and [Limitations](oidc-generic.md#limitations).

### Keycloak: `email_verified`

Keycloak sets `email_verified` from the per-user “Email Verified” flag. Users created via API, imported, or brokered from another IdP may stay `false` until Keycloak’s email verification (realm “Verify Email”), an admin sets the flag, or the upstream IdP uses **Trust Email** so Keycloak trusts the address. Prefer `"require_email_verified": true` once Keycloak reliably emits `email_verified=true` for your users.
