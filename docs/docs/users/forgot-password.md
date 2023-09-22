---
title: Forgot your SysReptor Password?
---

# Forgot Password?
:octicons-server-24: Self-Hosted

You can reset your password via the command line.  
Go to `sysreptor/deploy` and run:

```shell linenums="1"
username=reptor
docker compose exec app python3 manage.py changepassword "$username"
```
