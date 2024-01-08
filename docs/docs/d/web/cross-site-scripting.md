---
search:
  exclude: true
---

# Cross-site scripting (XSS)
## Description
Cross-site scripting (XSS) is a web security vulnerability where an attacker can inject malicious scripts into the HTML structure of a website due to insufficient validation or encoding of data. In XSS attacks, attackers embed JavaScript code in the content delivered by the vulnerable web application.

There are three different types of XSS:

### Stored XSS
Stored XSS is usually the most critical XSS vector. Attackers thereby place JavaScript code on pages visited by other users. The injected scripts execute in the users' web browsers when they visit the website.

### Reflected XSS
The goal of reflected XSS is to lure legitimate users to manipulated links and thus execute injected scripts. The most common method for this is a phishing email. When the victim opens the crafted link in a web browser, the HTTP request sends the malicious script to the web application. Due to insufficient validation and encoding, the web application accepts the injected script and embeds it as content in the subsequent response to the client. The malicious script executes in the victim's web browser and can potentially access cookies, session tokens, or other sensitive information.
Attackers can exploit reflected XSS on a larger scale, for example, by combining the attack with cache poisoning or HTTP request smuggling.

### DOM-based XSS
DOM-based XSS occurs when a web application contains client-side JavaScript code that insecurely processes data from untrusted sources (for example, when data is dynamically written back to the DOM of the web browser at runtime). It differs from reflected or stored XSS by how attackers inject malicious scripts into the HTML code. For reflected XSS and stored XSS attacks, server-side processes include the malicious scripts in the HTML code, but the web browser does so in DOM-based XSS. Sometimes, the browser does not even send the malicious script to the web server. Such an attack will bypass all server-side filtering measures to protect users. 

The victim's web browser executes malicious XSS scripts that can potentially access cookies, session tokens, or other sensitive information or trigger actions on behalf of the attacked user. An attacker gains control over web application functions and data in the victim's context. If the affected user has privileged access, an attacker may be able to gain complete control over the web application.

## Recommendation
* Filter untrusted user inputs as strictly as possible. Filtering and validation should happen based on expected and valid inputs.
* Encode data before including it in HTTP responses.
* Use a Content Security Policy (CSP) to control which client-side scripts are allowed and which are forbidden.
* Set the `HttpOnly` flag for sensitive cookies to prevent JavaScript access.
* Find detailed information on preventing XSS in the OWASP [Cross-Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).