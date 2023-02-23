# Open ID Connect Setup with Azure AD

## Preparation in Azure AD
1. Open [Microsoft Entra Admin Center](https://entra.microsoft.com)
2. Select Applications -> App registrations -> New registration
3. In following Menu: 

    - enter a Name for your reference (1)
    - select the types of accounts who are allowed to login (2) - this is the first option "Sigle tenant" in most cases
    - enter the redirect url of your application in the following format: https://your.url/login/oidc/azure/callback (3)
    - select type "Web" for redirect url (4)

    ![Register application menu](/images/oidc_1_register.png)

4. In the newly created "App registration", go to the Token configuration submenu and add the following *optional* claim:
    - TokenType: ID
    - Claims: auth_time, login_hint
    ![Register application menu](/images/oidc_2_claims.png)


5. Next go to the "Certificates & secrets" - Submenu and add a new client secret with 24 months validity(this is the maximum) and any description.
6. Copy the value of the newly created secret and store it for later use
7. Finally go to the "Overview" - Submenu and copy the values *Application (client) ID* and *Directory (tenant) ID*

You should now have the following values:

* client id
* client secret
* azure tendant id

## SaaS Setup

You are lucky, just send the values from the previous steps to us and we will take care of everything :)

## OnPrem Setup
