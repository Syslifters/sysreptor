---
grammarly: false
search:
  exclude: true
---

# Network Access Control
## Description
Network Access Control (NAC) allows you to define and enforce policies for access into a corporate network. For example, when a computer connects to a network, it is only allowed to access resources if it meets the policy set by the company (e.g., virus protection, current system version, specific configuration, etc.). Once the policy is met, the computer can access network resources and the Internet within the policy set by the NAC solution. The basic form of NAC is the 802.1X standard. 

802.1X is an authentication standard for devices that want to connect to a protected LAN or WIFI. Only authenticated and authorized devices can gain access to protected networks. Three components are involved in 802.1X authentication: a supplicant, an authenticator, and an authentication server. The supplicant is a device (e.g. a laptop) that wants to connect to the LAN or WIFI. The Authenticator is a network device (e.g. a switch or access point) that establishes the connection between the client and the network. The Authentication Server is a server that authenticates supplicants (i.e., client devices) and decides whether to allow a supplicant access to a protected network. The Authentication Server is connected to an identity store (such as LDAP) for this purpose.

The Extensible Authentication Protocol (EAP) is used for authentication, which provides a secure method of transmitting credentials for network authentication. 802.1X is the standard used to transmit EAP messages over wired or wireless networks.  Using an encrypted EAP tunnel, 802.1X prevents information from being read by third parties. The EAP protocol offers various authentication options such as via username/password (EAP-TTLS/PAP and PEAP-MSCHAPv2) or via client certificates (EAP-TLS).

## Recommendation
* Implement a NAC solution based on 802.1X to securely authenticate and authorize devices on your network.
* Use EAP-TLS to authenticate devices via certificates.
* Enforce MAC Authentication Bypass (MAB) for devices that do not support 802.1X. Ensures that these devices are compartmentalized using appropriate network segmentation. 
* Block network access for unknown devices by default.
* Asset management solutions can help detect unknown devices on the network.