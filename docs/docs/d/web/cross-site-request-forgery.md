---
search:
  exclude: true
---

# Cross-Site Request Forgery (CSRF)
## Description

Cross-site request forgery (CSRF) is a web security vulnerability in which an attacker can unknowingly trick an authenticated user into sending a state-changing HTTP request to the vulnerable web application. In CSRF, an attacker assumes the victim's identity and access privileges to perform unwanted actions (e.g., change email address) on their behalf. Without appropriate CSRF protection, the web application cannot distinguish between a request prepared by the attacker and a legitimate request from the victim.

Several prerequisites must be in place for a CSRF attack to take place. First, there must be an action in the web application that is relevant to an attacker and makes sense to exploit. For example, this could be a privileged action, such as changing a user's access permissions or a password. Another requirement is that no mechanism exists besides cookie-based authentication to distinguish HTTP requests from different users. Suppose the user is authenticated and thus has a valid session cookie. In that case, the web application cannot differentiate between a malicious, subverted request from the attacker and a legitimate request from the victim. Last, ensure that actions do not require specific parameters whose values an attacker cannot determine or predict. For example, if a user is asked to change his password, the function is not vulnerable if an attacker needs to know the value of the existing password.

A common way to exploit CSRF vulnerabilities is through phishing emails. An attacker does this by preparing malicious links to impose a state-changing request on the victim. The attacker then distributes the malicious links to victims via email. If an authenticated user opens the link in a web browser, the malicious website sends a cross-site request to the vulnerable web application. If successful, the attack causes an action with the victim's identity and privilege level.

## Recommendations
* Check if the framework has built-in CSRF protection and use it. If not, ensure that all state-changing requests contain a randomly generated CSRF token with high entropy. Also, validate CSRF tokens properly in the backend.
* Consider various additional security measures:
  * Use Custom Request Headers. By default, the browser's same-origin policy restricts JavaScript from submitting cross-site requests with custom HTTP request headers.
  * Set the `SameSite` attribute for session cookies to `strict`. Based on this attribute, web browsers decide whether to include cookies in cross-site requests.
  * User interactions such as CAPTCHAs, one-time tokens, re-authentication, etc., can also be considered as additional CSRF protection for highly sensitive actions. 
*  Find detailed information and assistance on preventing CSRF vulnerabilities in the [Cross-Site Request Forgery Cheat Sheet from OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).