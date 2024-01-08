---
search:
  exclude: true
---

# Resource-based Constrained Delegation (RBCD)
## Description
Resource-based Constrained Delegation (RBCD) is a particular type of Kerberos delegation configured in-depth for computer accounts. A computer account uses it to decide which other computers to trust for Kerberos delegations. This differs from the other types of delegation (Unconstrained and Constrained Delegation), configured on the computer accounts that want to access the resource (outbound). 

The attribute `msDS-AllowedToActOnBehalfOfOtherIdentity` controls RBCD by storing a security descriptor of the computer object that can access the resource. To abuse Resource-based Constrained Delegation, attackers define the `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute using the privileges of computer accounts over which they have control.

RBCD could, therefore, be exploited in this situation as follows:

1. Take over an account that is allowed to configure RBCD.
2. Add a new computer account to the domain
3. Set the `msDS-AllowedToActOnBehalfOfOtherIdentity` on the computer to be taken over.
    * To do this, define the Security Descriptor of the computer account from step 2 as the value.
4. Issue a service tick using resource-based constrained delegation.
5. Use the issued service ticket to compromise the computer.

## Recommendation
* Owners of a computer object should be Tier-0 user accounts.
* Domain users should not be allowed to add computers to the domain (`MachineAccountQuota` = 0).
    * Instead, a dedicated user account should be used, which should be considered as requiring special protection (cf. Domain Administrator).
* Add all sensitive user accounts to the Protected Users group.
* The option "Account is sensitive and cannot be delegated" should be activated for all computer accounts, if possible, and for all sensitive user accounts.