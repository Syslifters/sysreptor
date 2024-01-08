---
search:
  exclude: true
---

# Preboot Execution Environment
## Description

Preboot Execution Environment (PXE boot) is a network protocol that allows starting a computer via the network and providing an operating system or software without needing a local hard disk or optical drive. 

If misconfigured, PXE boot can be misused to open a shell with system authorizations when a new computer is started to create a local user with administrator authorizations. This allows the (often later domain-joined) device to be used with local administration authorizations.

To use PXE boot effectively and to automate the process of operating system provisioning, software tools like System Center Configuration Manager (SCCM) from Microsoft are often used. SCCM is a comprehensive management and deployment tool for IT infrastructures. It enables the central administration of operating systems, applications, and settings in a network.

With SCCM, administrators can set up PXE boot environments to configure computers on the network via network startup and automatically install operating systems or software. SCCM offers functions such as creating images, deploying software packages, collecting inventory data, and managing updates. It simplifies the process of operating system provisioning and enables centralized management and configuration of the network computers.

## Recommendation
* Disable the debug mode in boot images.
* If possible, only perform PXE deployments in isolated networks.
* Ensure that the password for starting the installation process is sufficiently secure.
