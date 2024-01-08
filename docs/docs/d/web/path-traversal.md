---
search:
  exclude: true
---

# Path traversal / Directory traversal
## Description
Path Traversal is a web security vulnerability that allows an attacker to access files and directories on the underlying web server of a web application. 
Access to files and directories in a path traversal attack is restricted solely by the existing access controls of the underlying operating system. Web servers usually limit access to a specific part of the file system: the "web root". This directory contains all files required for the functionality of the web application. Attackers use special strings in path specifications to break out of the web root folder using a path traversal attack. 

In the simplest form, an attacker uses the string "../" to change the location of the resource requested in the parameter. This string is a relative path specification. It refers specifically to the parent directory of the current working directory. Attackers also often use alternative encodings of the "../" sequence to bypass any security filters that may be in place. These methods include valid and invalid Unicode-encoded ("..%u2216" or "..%c0%af"), URL-encoded ("%2e%2e%2f"), and duplicate URL-encoded characters ("..%255c") of the backslash character. Advanced techniques also often use additional special characters such as the period "." to refer to the current working directory or the "%00" NULL character to bypass rudimentary end-of-file checks. 

In a successful attack, an attacker can use path traversal to access arbitrary files and directories on the vulnerable system. This may include sensitive operating system files, application code, or configuration files. Path Traversal may also provide write access to files and directories, sometimes allowing attackers to gain code execution and, thus, complete control over the web server.

## Recommendation
* Avoid using custom filenames and path specifications in the web application and use indexes instead (e.g., index: 5 corresponds to "images/img.png").
* Ensure that only valid and expected client input is accepted. Discard all other inputs.
* If you have to normalize paths, consider that characters may be single or multiple encoded (such as URL encoded, e.g., `%20` or `%2520` instead of a space).
