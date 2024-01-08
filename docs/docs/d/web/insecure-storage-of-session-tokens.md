---
search:
  exclude: true
---

# Insecure storage of session tokens
## Description
Web browsers have security mechanims for protecting session tokens. Those mechanisms prevent access to the session token via JavaScript and ensuring that the session token is always sent via encrypted channels. They are however only applicable to Cookies.

Web applications storing session tokens in the browser's session session storage, local storage or IndexDB make the session tokens readable via JavaScript. If tokens are stored in the local storage or IndexDB (instead of the session storage), the data is retained after the browser is closed. This further increases the risk because the tokens are retained even after the browser is closed.

Single-page apps (SPAs) require access tokens to call APIs. They often also have a refresh token that allows offline access to the users' resources. This refresh token can request new access tokens without user interaction and are a particularly interesting target in cross-site scripting (XSS) attacks.

If tokens with wide scopes are issued to the SPA, this can potentially give an attacker access to functionality not normally accessible through the user interface. In the event of theft, an attacker can at least take over the identity of the victim and perform actions.

## Recommendation
We advise against storing sensitive data such as session tokens in the session storage, local storage, or the IndexDB of the web browser.

* Prefer cookies with `Secure` and `HttpOnly` flags over other storage mechanisms.
* If this is not possible, consider setting the refresh token as a cookie.
* Prefer session storage over local storage and IndexDB.
* Consider a Backend-for-Frontend architecture. [^1] [^2] [^3]

[^1]: https://learn.microsoft.com/en-us/azure/architecture/guide/web/secure-single-page-application-authorization
[^2]: https://curity.io/resources/learn/the-token-handler-pattern/
[^3]: https://damienbod.com/2022/01/10/comparing-the-backend-for-frontend-bff-security-architecture-with-an-spa-ui-using-a-public-api/

