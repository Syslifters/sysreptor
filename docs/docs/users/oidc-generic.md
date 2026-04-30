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

## SysReptor Configuration

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
        "reauth_supported": false,
        "require_email_verified": true
    }
}
```

...and add it to your [application settings](/setup/configuration/#single-sign-on-sso):

```env
OIDC_AUTHLIB_OAUTH_CLIENTS='{"<your provider name>": {"label": "<human readable provider name>",...}}'
```

## Limitations
### Reauthentication
SysReptor reauthenticates users before critical actions. It therefore requires users to enter their authentication details (e.g. password and second factor, if configured).

Your OIDC provider might not support enforced reauthentication. Your can try to set `"reauth_supported": true`. If the "Enable Superuser Permissions" functionality does not work, set to this value to `false`.

When `"reauth_supported": true`, SysReptor attempts to trigger reauthentication by setting the OIDC parameters `prompt=login` and `max_age=0` on the authorization request. This enforced the user to log in again at the OIDC provider. SysReptor verifies that `auth_time` in the response indicates a recent authentication.

To enforce reauthentication, users can set a password for their local SysReptor user. This will enforce reauthentication with the local user's credentials.

### Verified Emails
If `"require_email_verified": true`, SysReptor requires the OIDC `email_verified` claim to be present and `true` for login. Some OIDC providers do not include this claim at all, or it may be `false` even if the user has an email address.

Setting `"require_email_verified": false` means SysReptor will not require proof of email ownership via the OIDC `email_verified` claim. This is fine for many IdPs because they only release verified email addresses. However, if your IdP can emit an unverified or user-controlled `email` (or `preferred_username`) claim, a user could set it to another person's email address and be logged in to SysReptor as that user (including any admin/superuser privileges).

