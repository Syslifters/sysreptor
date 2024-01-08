---
grammarly: false
search:
  exclude: true
---

# LSASS protection
## Description
The Local Security Authority Subsystem Service is a process in Microsoft Windows operating systems that is responsible for enforcing security policy on the system. For this purpose, among other things, it temporarily stores the credentials of logged-in users in order to perform authentications against other systems (e.g. when opening a file share).

Depending on the operating system version, either plain-text passwords or only NT hashes are stored by default. However, NT hashes are similarly critical as passwords, since they can be used for authentication via pass-the-hash.

To protect this critical process, the vendor provides several methods, including "Credential Guard" and "LSA Protection" (RunAsPPL).

Credential Guard is a virtualization-based isolation technology for LSASS in which credentials are stored in a memory area protected by the processor. Access to credentials protected in this way is not possible. However, you should note that this only protects credentials that are already cached. An attacker could still intercept the credentials of new authentication processes.

LSA Protection (RunAsPPL) is a protection mechanism in the Windows kernel that protects the memory of the LSASS process from access. However, since this is a kernel feature, it can be bypassed by kernel modules. It should still be enabled along with Credential Guard. Loading a malicious kernel module provides versatile opportunities for AV/EDR/HIDS systems to detect the attack, making the attack more difficult.

## Recommendation
Credential Guard and LSA Protection should be enabled on all systems.