---
search:
  exclude: true
---

# Insecure HTTP cookies
## Description
HTTP is a stateless protocol, meaning it cannot distinguish requests from different users without an additional mechanism. Addressing this problem requires a session mechanism. The most commonly used mechanism for managing HTTP sessions in browsers is cookie storage. An HTTP cookie is a small record that a server sends to a user's web browser. The browser can store the cookie and send it back to the same server for subsequent requests. Web applications can thus implement sessions for the stateless HTTP protocol. The server can use the HTTP cookie to distinguish requests from different users and to keep users logged in. 

Cookies thus represent a frequent target for attackers. A web application should, therefore, harden the configuration of all sensitive cookies by setting the `Secure` and `HttpOnly` cookie attributes and the `SameSite` attribute to `strict`:

* A cookie with the `Secure` attribute will only be sent to the server over HTTPS connections and never over an unsecured HTTP connection.
* A cookie with the `HttpOnly` attribute set is inaccessible to JavaScript and thus helps mitigate cross-site scripting (XSS) attacks.
* A cookie with `SameSite=strict` attribute will not be sent in cross-site requests from third-party websites (in contrast to the weaker `Lax` and the insecure `None`). 

If an attacker can tap sensitive cookies such as session cookies, the attacker could take over user accounts and perform actions in the context of affected users. An attacker may also gain complete control over all web application functions and data if they take over a user account with privileged access.

## Recommendation
Set the cookie attributes `HttpOnly`, `Secure`, and `SameSite=Strict`.