# SSO Setup with OIDC
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

1. Configure your Identity Provider (IDP) and add configuration details to your `app.env`
    * [Azure Active Directory](../../setup/oidc-azure-active-directory)
    * [Google Workplace/Google Identity](../../setup/oidc-google)
    * [Keycloak](../../setup/oidc-keycloak)
    * [Generic OIDC setup](../../setup/oidc-generic)
    * Need documentation for another IDP? Drop us a message at [GitHub Discussions](https://github.com/Syslifters/sysreptor/discussions/categories/ideas){ target=_blank }!
3. Restart containers using `docker-compose up -d` in `deploy` directory
2. Set up local users:

    a. Create user that should use SSO  
    b. Go to "Identities"  
    c. Add identity ("Add")  
    d. Select Provider and enter the email address used at your IDP (note: the identifier is case sensitive and has to be the same case as in the SSO provider)

![Add SSO identity](../../images/add_identity.png)

The user can now login via his IDP.
