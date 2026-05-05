---
title: Generic OIDC Configuration
---

# Generic OIDC Configuration
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Configuration at your OIDC provider
1. Create a `client_id` and a `client_secret` in your OIDC provider
2. Add the callback-url: `https://`<your-sysreptor-url>/login/oidc/<sso-provider-id>/callback`
    * Add the hostname where your SysReptor installation can be accessed.
    * Choose a custom **SSO provider id** (top-level key in `OIDC_AUTHLIB_OAUTH_CLIENTS`, e. g. `keycloak`).


## SysReptor Configuration

`OIDC_AUTHLIB_OAUTH_CLIENTS` is one JSON object. Each **top-level key** is an **SSO provider id**: it identifies this IdP in SysReptor (login URL, user SSO identity **Provider** field, `DEFAULT_AUTH_PROVIDER`, etc.). Choose a stable id (for example `keycloak`, `google`, `entra`).

```json
{
    "<sso-provider-id>": {
        "label": "<human readable provider name>",
        "client_id": "<your client_id>",
        "client_secret": "<your_client_secret>",
        "server_metadata_url": "<link to OIDC provider's openid-configuration>",
        "client_kwargs": {
            "scope": "openid email",
            "code_challenge_method": "S256"
        },
        "reauth_supported": false,
        "user_identifier_claim": "email",
        "require_email_verified": true
    }
}
```

...and add it to your [application settings](/setup/configuration/#single-sign-on-sso) (`OIDC_AUTHLIB_OAUTH_CLIENTS`).


### OIDC Config JSON {#oidc-authlib-json}

The **SSO provider id** (each JSON object key) names one OIDC connection. Its value is one inner configuration object. SysReptor registers that object with [Authlib](https://docs.authlib.org/en/stable/oauth2/client/web/index.html):

* `label`: Display name of the OIDC provider. Shown on the login screen.
* `client_id`: OAuth 2.0 client identifier from the IdP.
* `client_secret`: OAuth 2.0 client secret from the IdP.
* `server_metadata_url`: Discovery document URL (OpenID Provider Metadata, usually `https://example.com/.../.well-known/openid-configuration`).
* `client_kwargs`: Arguments passed to the OAuth client (for example `scope` and `code_challenge_method` for PKCE on the authorization request).

SysReptor-specific:

* `user_identifier_claim`: Which UserInfo field is the user's SSO identifier (default `email`). See [User identifier claim](#user-identifier-claim).
* `require_email_verified`: When `user_identifier_claim` is `email`, require `email_verified` to be true in UserInfo. See [Verified Emails](#verified-emails).
* `reauth_supported`: If `true`, SysReptor may use `prompt=login` and `max_age=0` for sensitive reauthentication when the IdP supports it. See [Reauthentication](#reauthentication).

### User identifier claim {#user-identifier-claim}

After OIDC login, SysReptor looks up one claim in the IdP’s UserInfo response. The setting `user_identifier_claim` is the **claim name** (for example `email` or `sub`). If you omit it, SysReptor uses `email`.

That claim’s **value** is the string SysReptor compares to each user’s saved SSO identity for this same provider (User management → Identities). It must match **exactly**, including upper- and lowercase. The IdP must return the claim (scopes and IdP configuration); otherwise login cannot find a user.

If the claim name is `email`, the separate `require_email_verified` option applies (see [Verified Emails](#verified-emails)).

!!! warning "Account takeover risk"

    If the IdP lets users change the chosen UserInfo field without verification (e.g. `preferred_username` for some IdPs), an attacker can set that value to another user’s stored SSO identifier and SysReptor will log them in as that account—including privileged users. Prefer claims the IdP assigns and does not let end users repoint freely; avoid profile-style fields users can edit to arbitrary values.

### Verified Emails
If `"require_email_verified": true`, SysReptor requires the OIDC `email_verified` claim to be present and `true` for login. Some OIDC providers do not include this claim at all, or it may be `false` even if the user has an email address.

Setting `"require_email_verified": false` means SysReptor will not require proof of email ownership via the OIDC `email_verified` claim. This is fine for many IdPs because they only release verified email addresses. However, if your IdP can emit an unverified or user-controlled `email` (or `preferred_username`) claim, a user could set it to another person's email address and be logged in to SysReptor as that user (including any admin/superuser privileges).

### Reauthentication
SysReptor reauthenticates users before critical actions. It therefore requires users to enter their authentication details (e.g. password and second factor, if configured).

Your OIDC provider might not support enforced reauthentication. You can try `"reauth_supported": true`. If the "Enable Superuser Permissions" flow does not work, set it to `false`.

When `"reauth_supported": true`, SysReptor attempts to trigger reauthentication by setting the OIDC parameters `prompt=login` and `max_age=0` on the authorization request. This forces a fresh login at the OIDC provider. SysReptor verifies that `auth_time` in the response indicates a recent authentication.

To enforce reauthentication, users can set a password for their local SysReptor user. This will enforce reauthentication with the local user's credentials.

