# Direct Memory Access
## Description
Direct Memory Access (DMA) enables hardware devices such as network cards or USB controllers to access the system's main memory directly without involving the CPU. This allows faster data transfers.

In a DMA attack, an attacker uses physical or remote access to a target system and takes advantage of the DMA capabilities to access the RAM directly. This access allows the attacker to bypass traditional security measures such as operating system permissions or encryption and potentially gain unauthorized access to sensitive data or compromise the system's integrity.

There are two main types of DMA attacks:

1. DMA read attacks: The attacker gains access to the system's memory and can read sensitive information from memory, such as encryption keys, passwords, or confidential data. The attacker can then use this information for unauthorized purposes.

2 DMA write attacks: The attacker injects malicious data or code into the system's memory and overwrites potentially critical data or alters the system's behavior. This can lead to privilege escalation, malware injection, or changes to system settings.

DMA attacks can be carried out in various ways, including physical access to the target system, compromised peripherals, or exploiting vulnerabilities in the system firmware or drivers. Some examples of DMA attack vectors are FireWire, Thunderbolt, PCI Express, or PCMCIA interfaces.

## Recommendation
Activate the Windows function "Kernel DMA Protection" to protect against DMA attacks.