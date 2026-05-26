# SSO Setup with OIDC
<BadgePro />

1. Configure your Identity Provider (IDP) and add configuration details to your [application settings](/setup/configuration#single-sign-on-sso).
    * [Microsoft Entra ID](/users/oidc-entra-id)
    * [Google Workplace/Google Identity](/users/oidc-google)
    * [Keycloak](/users/oidc-keycloak)
    * [Generic OIDC setup](/users/oidc-generic)
    * Need documentation for another IDP? Drop us a message at [GitHub Discussions](https://github.com/Syslifters/sysreptor/discussions/categories/ideas)!
2. Set up local users:

    a. Create user that should use SSO  
    b. Go to "Identities"  
    c. Add identity ("Add")  
    d. Select Provider and enter the SSO identifier provided by your IdP (default: `email`, configurable via `user_identifier_claim`). Matching is case-sensitive and must use the same spelling and casing as the IdP returns.

![Add SSO identity](/images/add_identity.png)

The user can now log in via their IdP.
