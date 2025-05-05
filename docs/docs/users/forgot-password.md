---
title: Forgot your SysReptor Password?
---

# Forgot Password?

## Reset Password via Forgot Password Email
:octicons-server-24: Self-Hosted :octicons-cloud-24: Cloud

If you've forgotten your password, you can reset it via email by following these steps:

1. Visit the SysReptor login page at `https://sysreptor.example.com/login/`
2. Click on the "Forgot Password?" link below the login form
3. Enter your email address of your SysReptor account
4. We will send you an email with a link to reset your password
5. Click on the reset password link in the email
6. On the password reset page, enter your new password and confirm it
7. You can now log in with your new password

!!! info
    [Email sending](/setup/configuration#emails) and [`FORGOT_PASSWORD_ENABLED`](/setup/configuration#local-user-authentication) need to be configured.
    Your user also needs to have an email address set.



## Reset Password via User Admin Interface
:octicons-server-24: Self-Hosted :octicons-cloud-24: Cloud

Administrators with superuser or user manager permissions can reset passwords for any user through the admin interface at `https://sysreptor.example.com/users/<user-id>/reset-password/`:

1. Log in to SysReptor with an account that has [superuser](/users/user-permissions/#superuser) or [user manager permission](/users/user-permissions/#user-manager)
2. Navigate to the Users section by clicking on "Users" in the main navigation menu
3. Find and select the user whose password needs to be reset in the user list
4. Click on the "Reset Password" button for that user
5. Set a new password for the user. You can also check "Must change password" to force the user to change their password upon their next login
6. The user can now log in with the new password



## Reset Password via CLI 
:octicons-server-24: Self-Hosted

As a last resort, you can reset your password via the command line.  
Go to `sysreptor/deploy` and run:

```shell
docker compose exec app python3 manage.py changepassword "<username>"
```
