# SQL injection (SQLi)
## Description
SQL Injection is a server-side vulnerability in web applications. It occurs when software developers create dynamic database queries that contain user input. To exploit this vulnerability, an attacker can craft user input so that the originally intended action of an SQL statement is changed. SQL injection vulnerabilities result from an application's failure to dynamically create database queries insecurely and to validate user input properly. The SQL language does not distinguish between control characters and data characters. Control characters in the data part of SQL statements must be encoded or escaped appropriately beforehand.

Attackers often detect SQL injection vulnerabilities by inserting a control character (like a single apostrophe) into the user input to place new commands not present in the original SQL statement. A simple example demonstrates this process. The following SELECT statement contains a variable userId. This statement aims to get a user's data with a specific user ID from the Users table.

`sqlStmnt = 'SELECT * FROM Users WHERE UserId = ' + userId;`

An attacker could now use special user input to change the original intent of the SQL statement. For example, he could use the string `' or 1=1` as user input. In this case, the application would construct the following SQL statement:

`sqlStmnt = 'SELECT * FROM Users WHERE UserId = ' + ' or 1=1;`

Instead of a user's data with a specific user ID, the database returns data of all users in the table. This allows an attacker to control the SQL statement in his favor. 

Several variants of SQL injection vulnerabilities, attacks, and techniques occur in different situations depending on the database system used. However, they all share that the database interprets user input as SQL commands (as in the example above). Successful SQL injection attacks can have far-reaching consequences. One would be the loss of confidentiality and integrity of the stored data. Attackers could gain read and possibly write access to sensitive data in the database. SQL injection could also compromise the authentication and authorization of the web application, allowing attackers to bypass existing access controls. In some cases, SQL injection can also be used to execute operating system commands, allowing an attacker to gain complete control over the vulnerable server.

## Recommendation
