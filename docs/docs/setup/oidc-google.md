---
title: Google OIDC Configuration
---

# Google OIDC Configuration
<span style="color:red;">:octicons-heart-fill-24: Pro only</span>

## Configuration at Google
1. Open [Google Cloud Console](https://console.cloud.google.com/){ target=_blank }
    - Make sure to select the correct organization:

    ![Google Cloud Console Organization](/images/google_cloud_console.png){ style="width: 60%" }

2. Use search box and click "Create a Project"

    ![Click "Create a Project"](/images/google_call_create_project.png){ style="width: 60%" }

3. Enter Name, Organization, Location and "Create"

    ![Enter project details](/images/google_create_project.png){ style="width: 60%" }

4. Search for and call "OAuth consent screen"
5. Select "Internal" for "User Type" and "Create"

    ![Select "User Type" "Internal"](/images/google_user_type_internal.png){ style="width: 60%" }

6. Enter "App information"

    ![Enter App information](/images/google_app_information.png){ style="width: 60%" }

7. Optional: Add App logo

    - You can use [this](/images/sysreptor_120x120.png){ style="width: 60%" }

8. Enter App domain info

    ![App domain info](/images/google_app_domain.png){ style="width: 60%" }

9. Enter Developer contact information and click "Save and Continue"

    ![Add contact information and continue](/images/google_developer_info.png){ style="width: 60%" }

10. Add the scopes `email`, `profile`, `openid` (don't forget to click "Update")

    ![Add scopes](/images/google_add_scopes.png){ style="width: 60%" }

11. Click "Save and Continue" and verify your data
12. Go to "Credentials", "Create Credentials" and select "OAuth client ID"

    ![Create credentials](/images/google_create_credentials.png){ style="width: 60%" }

13. Select "Web Application" at "Application type" and enter a name

    ![Enter client details](/images/google_client_data.png){ style="width: 60%" }

14. You don't need any JavaScript origins
15. Enter the URL to your SysReptor installation with the path `/login/oidc/google/callback` as Authorized redirect URI

    ![Enter redirect URL](/images/google_authorized_redirect_uri.png){ style="width: 60%" }

16. Click "Create"

You should now have the following values:

* Client ID
* Client secret


## Cloud Setup
:octicons-cloud-24: Cloud

You are lucky. Just send the values from the previous steps to us and we'll take care :smiling_face_with_3_hearts:


## Self-Hosted Setup
:octicons-server-24: Self-Hosted

The values from the previous steps need to be passed as environment variables to the SysReptor docker container.
You can add them to `<sysreptor-repository>/deploy/app.env`:
```env
OIDC_GOOGLE_CLIENT_ID=<google client id>
OIDC_GOOGLE_CLIENT_SECRET=<google client secret>
```

The OIDC client needs to be able to establish a network connection to Google.
Make sure to not block outgoing traffic.

Restart the docker container by going to `sysreptor/deploy` and:

```shell linenums="1"
docker compose up -d
```

## Limitations
SysReptor reauthenticates users before critical actions. It therefore requires users to enter their authentication details (e.g. password and second factor, if configured).

Google does not support enforced reauthentication. The reauthentication therefore redirects to Google. If the users are still authenticated at Google, they are redirected back and SysReptor regards the reauthentication as successful.

This is a limitation by Google.

To enforce reauthentication, users can set a password for their local SysReptor user. This will enforce reauthentication with the local user's credentials.
