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
        "require_email_verified": false
    }
}
```

...and add it to your [application settings](/setup/configuration/#single-sign-on-sso):

```env
OIDC_AUTHLIB_OAUTH_CLIENTS='{"keycloak": {"label": "Keycloak",...}}'
```

The OIDC client needs to be able to establish a network connection to Keycloak.
Make sure to not block outgoing traffic.


## Limitations
### Reauthentication
SysReptor reauthenticates users before critical actions. It therefore requires users to enter their authentication details (e.g. password and second factor, if configured).

Your Keycloak installation might not support enforced reauthentication. Your can try to set `"reauth_supported": true`. If the "Enable Superuser Permissions" functionality does not work, set to this value to `false`.

When `"reauth_supported": true`, SysReptor attempts to trigger reauthentication by setting the OIDC parameters `prompt=login` and `max_age=0` on the authorization request. This enforced the user to log in again at the OIDC provider. SysReptor verifies that `auth_time` in the response indicates a recent authentication.

To enforce reauthentication, users can set a password for their local SysReptor user. This will enforce reauthentication with the local user's credentials.


### Verified Email
Keycloak’s `email_verified` claim is derived from the per-user "Email Verified" flag. Users created/provisioned via API or imported/brokered from external identity providers may have this set to `false` unless they complete Keycloak’s email verification flow (realm setting "Verify Email"), an administrator sets the flag to `true`, or the external identity provider is configured with "Trust Email" (so Keycloak trusts the email and skips verification for those users).
Using `"require_email_verified": false` is usually fine when Keycloak (and any upstream brokered IdP) only releases verified email addresses. However, if users can set/change their email without verification, a user could set their `email` claim to another person's email address and be logged in to SysReptor as that user (including any admin/superuser privileges).

Prefer `"require_email_verified": true` and ensure Keycloak emits `email_verified=true` for all users (e.g., enable "Verify Email", set "Email Verified" appropriately, or only "Trust Email" for upstream IdPs that actually verify email ownership).
