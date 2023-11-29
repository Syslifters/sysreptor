# Insecure name resolution protocols
## Description
An attacker gets into a MitM position if, for example, he is able to manipulate the name resolution in a network. This is the case if an attacker has direct access to the network. The Link-Local Multicast Name Resolution (LLMNR), NetBIOS Name Service (NBT-NS) or Multicast DNS (mDNS) protocols are, in addition to Domain Name System (DNS), three alternative ways of resolving host names in a network. 

Name resolutions via such broadcast protocols can be very easily manipulated by an attacker. An attacker responds to all requests in the network with the address of a system under his control, forcing communication with this system. If the requested host requires authentication, the user name and the Net-NTLMv2 hash are sent to the system controlled by the attacker. Net-NTLMv2 hashes can thus be intercepted and used in the course of relaying attacks.

An attacker may then be able to access the target system and execute code there. Furthermore, Net-NTLM hashes are susceptible to offline brute force attacks. Attackers can try out password combinations at very high speeds and obtain the plain text password in the event of a successful attack.

## Recommendation
Disable LLMNR, NBT-NS, and mDNS name resolutions in the local computer security settings or via Group Policy.