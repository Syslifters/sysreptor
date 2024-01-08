---
grammarly: false
search:
  exclude: true
---

# Insecure ADIDNS
## Description
Domain controller DNS can store its zone data in Active Directory Domain Services (AD DS). There is no need for a separate DNS replication topology like DNS zone transfers. Any domain controller in a domain running the DNS server service can update the DNS zones built into Active Directory. All zone data is automatically replicated by Active Directory replication with domain controllers. 

ADIDNS zones can be modified remotely via dynamic updates or by using LDAP. DNS Dynamic Update Protocol is a DNS-specific protocol designed for updating DNS zones. In Active Directory, dynamic updates are mainly used by computer accounts to add and update their own DNS records. New records can be added to the zone if they do not already exist. Accounts that create new records are given full control over them. User accounts cannot edit existing records or add another record with the same name by default, even if the record type is different (A, AAAA, CNAME, MX, etc.).

By default, ADIDNS zone access permissions allow regular domain users to create new DNS records that do not yet exist. If zones are configured for insecure dynamic updates, unauthenticated users can modify all existing DNS records. Attackers can exploit both circumstances to get into a MitM position. 

For example, an attacker could add a new record to a DNS zone when a client on the network resolves a name via Link-Local Multicast Name Resolution (LLMNR) or NetBIOS Name Service (NBT-NS). A name that is resolved via LLMNR or NBT-NS typically does not exist in DNS. Alternatively, if DNS zones are configured for insecure dynamic updates, an attacker can modify existing DNS records. This allows an attacker to ensure that clients resolve a specific name using DNS with an arbitrary IP address. If an attacker is in this position, network traffic between two systems can be routed through a system controlled by the attacker, as in any other spoofing attack. In a successful attack, an attacker could obtain credentials to remotely execute code on a Windows machine or move laterally on the network.

## Recommendation
* Restrict DNS zone access permissions to prevent authenticated users from creating new DNS records.
* Ensure that only secure dynamic DNS updates are allowed.
* Use a dedicated user account for dynamic DNS updates via DHCP.
* Create a wildcard (`*`), as well as a `wpad` record (e.g. as a TXT record) in all zones.
* Mail clients should not load images by default, at least from external senders.