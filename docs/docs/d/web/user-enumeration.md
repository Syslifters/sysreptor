---
search:
  exclude: true
---

# User enumeration
## Description
Web applications sometimes indicate whether a username or e-mail address exists as a user. Two of the most common places this occurs are the web application's login page or the "forgot password" functionality. For example, users who enter incorrect credentials receive the information that their password was wrong. An attacker can now use the information to determine whether a particular username exists. An attacker can now use the data to specify a list of valid usernames. 

Once attackers have such a list, they can address these user accounts in new attacks to obtain valid credentials. In its simplest form, an attacker could perform password-guessing attacks. Attackers can use large word lists containing frequently used passwords for this. An attacker could also use enumerated usernames to search past data leaks for passwords. Credentials from data leaks, consisting of pairs of usernames and passwords, can be reused by attackers in automated attacks. This particular form of brute force attack is also known as credential stuffing. Alternatively, an attacker can use usernames during social engineering campaigns to contact users.

## Recommendation
* Ensure the web application returns generic error messages when users enter invalid credentials.
* Ensure that web server response times are similar for valid and invalid user accounts.
