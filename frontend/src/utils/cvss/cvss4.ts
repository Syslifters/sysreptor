/* eslint-disable camelcase */
import { CvssVersion } from "./base";
import type { CvssDefinition, CvssMetricsValue, CvssMetricsValueCollection } from "./base";

export const CVSS40_DEFINITION: CvssDefinition = Object.freeze({ 
  AV: { 
    id: 'AV', 
    name: 'Attack Vector', 
    description: 'This metric reflects the context by which vulnerability exploitation is possible. This metric value (and consequently the resulting severity) will be larger the more remote (logically, and physically) an attacker can be in order to exploit the vulnerable system. The assumption is that the number of potential attackers for a vulnerability that could be exploited from across a network is larger than the number of potential attackers that could exploit a vulnerability requiring physical access to a device, and therefore warrants a greater severity.', 
    choices: [
      { 
        id: 'N', 
        name: 'Network', 
        description: 'The vulnerable system is bound to the network stack and the set of possible attackers extends beyond the other options listed below, up to and including the entire Internet. Such a vulnerability is often termed “remotely exploitable” and can be thought of as an attack being exploitable at the protocol level one or more network hops away (e.g., across one or more routers).' 
      }, 
      { 
        id: 'A', 
        name: 'Adjacent',
        description: 'The vulnerable system is bound to a protocol stack, but the attack is limited at the protocol level to a logically adjacent topology. This can mean an attack must be launched from the same shared proximity (e.g., Bluetooth, NFC, or IEEE 802.11) or logical network (e.g., local IP subnet), or from within a secure or otherwise limited administrative domain (e.g., MPLS, secure VPN within an administrative network zone).' 
      }, 
      { 
        id: 'L', 
        name: 'Local',
        description: 'The vulnerable system is not bound to the network stack and the attacker’s path is via read/write/execute capabilities. Either the attacker exploits the vulnerability by accessing the target system locally (e.g., keyboard, console), or through terminal emulation (e.g., SSH); or the attacker relies on User Interaction by another person to perform actions required to exploit the vulnerability (e.g., using social engineering techniques to trick a legitimate user into opening a malicious document).' 
      }, 
      { 
        id: 'P', 
        name: 'Physical',
        description: 'The attack requires the attacker to physically touch or manipulate the vulnerable system. Physical interaction may be brief (e.g., evil maid attack) or persistent.' 
      }
    ] 
  },
  AC: { 
    id: 'AC', 
    name: 'Attack Complexity',
    description: 'This metric captures measurable actions that must be taken by the attacker to actively evade or circumvent existing built-in security-enhancing conditions in order to obtain a working exploit. These are conditions whose primary purpose is to increase security and/or increase exploit engineering complexity. A vulnerability exploitable without a target-specific variable has a lower complexity than a vulnerability that would require non-trivial customization. This metric is meant to capture security mechanisms utilized by the vulnerable system.',
    choices: [{ 
      id: 'L', 
      name: 'Low', 
      description: 'The attacker must take no measurable action to exploit the vulnerability. The attack requires no target-specific circumvention to exploit the vulnerability. An attacker can expect repeatable success against the vulnerable system.' 
    }, 
    { 
      id: 'H', 
      name: 'High',
      description: 'The successful attack depends on the evasion or circumvention of security-enhancing techniques in place that would otherwise hinder the attack. These include: Evasion of exploit mitigation techniques, for example, circumvention of address space randomization (ASLR) or data execution prevention (DEP) must be performed for the attack to be successful; Obtaining target-specific secrets. The attacker must gather some target-specific secret before the attack can be successful. A secret is any piece of information that cannot be obtained through any amount of reconnaissance. To obtain the secret the attacker must perform additional attacks or break otherwise secure measures (e.g. knowledge of a secret key may be needed to break a crypto channel). This operation must be performed for each attacked target.' 
    }] 
  },
  AT: { 
    id: 'AT', 
    name: 'Attack Requirements',
    description: 'This metric captures the prerequisite deployment and execution conditions or variables of the vulnerable system that enable the attack. These differ from security-enhancing techniques/technologies (ref Attack Complexity) as the primary purpose of these conditions is not to explicitly mitigate attacks, but rather, emerge naturally as a consequence of the deployment and execution of the vulnerable system.',
    choices: [
      { 
        id: 'N', 
        name: 'None',
        description: 'The successful attack does not depend on the deployment and execution conditions of the vulnerable system. The attacker can expect to be able to reach the vulnerability and execute the exploit under all or most instances of the vulnerability.' 
      }, 
      { 
        id: 'P', 
        name: 'Present',
        description: 'The successful attack depends on the presence of specific deployment and execution conditions of the vulnerable system that enable the attack. These include: a race condition must be won to successfully exploit the vulnerability (the successfulness of the attack is conditioned on execution conditions that are not under full control of the attacker, or the attack may need to be launched multiple times against a single target before being successful); the attacker must inject themselves into the logical network path between the target and the resource requested by the victim (e.g. vulnerabilities requiring an on-path attacker).' 
      }] 
  },
  PR: {
    id: 'PR',
    name: 'Privileges Required', 
    description: 'This metric describes the level of privileges an attacker must possess prior to successfully exploiting the vulnerability. The method by which the attacker obtains privileged credentials prior to the attack (e.g., free trial accounts), is outside the scope of this metric. Generally, self-service provisioned accounts do not constitute a privilege requirement if the attacker can grant themselves privileges as part of the attack.',
    choices: [{
      id: 'N',
      name: 'None', 
      description: 'The attacker is unauthorized prior to attack, and therefore does not require any access to settings or files of the vulnerable system to carry out an attack.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'The attacker requires privileges that provide basic capabilities that are typically limited to settings and resources owned by a single low-privileged user. Alternatively, an attacker with Low privileges has the ability to access only non-sensitive resources.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'The attacker requires privileges that provide significant (e.g., administrative) control over the vulnerable system allowing full access to the vulnerable system’s settings and files.' 
    }] 
  },
  UI: {
    id: 'UI',
    name: 'User Interaction', 
    description: 'This metric captures the requirement for a human user, other than the attacker, to participate in the successful compromise of the vulnerable system. This metric determines whether the vulnerability can be exploited solely at the will of the attacker, or whether a separate user (or user-initiated process) must participate in some manner.',
    choices: [{
      id: 'N',
      name: 'None', 
      description: 'The vulnerable system can be exploited without interaction from any human user, other than the attacker.' 
    }, {
      id: 'P',
      name: 'Passive', 
      description: 'Successful exploitation of this vulnerability requires limited interaction by the targeted user with the vulnerable system and the attacker’s payload. These interactions would be considered involuntary and do not require that the user actively subvert protections built into the vulnerable system.' 
    }, {
      id: 'A',
      name: 'Active', 
      description: 'Successful exploitation of this vulnerability requires a targeted user to perform specific, conscious interactions with the vulnerable system and the attacker’s payload, or the user’s interactions would actively subvert protection mechanisms which would lead to exploitation of the vulnerability.' 
    }] 
  },
  VC: {
    id: 'VC',
    name: 'Confidentiality', 
    description: 'This metric measures the impact to the confidentiality of the information managed by the VULNERABLE SYSTEM due to a successfully exploited vulnerability. Confidentiality refers to limiting information access and disclosure to only authorized users, as well as preventing access by, or disclosure to, unauthorized ones.',
    choices: [{
      id: 'H',
      name: 'High', 
      description: "There is a total loss of confidentiality, resulting in all information within the Vulnerable System being divulged to the attacker. Alternatively, access to only some restricted information is obtained, but the disclosed information presents a direct, serious impact. For example, an attacker steals the administrator's password, or private encryption keys of a web server." 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'There is some loss of confidentiality. Access to some restricted information is obtained, but the attacker does not have control over what information is obtained, or the amount or kind of loss is limited. The information disclosure does not cause a direct, serious loss to the Vulnerable System.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'There is no loss of confidentiality within the Vulnerable System.' 
    }] 
  },
  VI: {
    id: 'VI',
    name: 'Integrity', 
    description: 'This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information. Integrity of the VULNERABLE SYSTEM is impacted when an attacker makes unauthorized modification of system data. Integrity is also impacted when a system user can repudiate critical actions taken in the context of the system (e.g. due to insufficient logging).',
    choices: [{
      id: 'H',
      name: 'High', 
      description: 'There is a total loss of integrity, or a complete loss of protection. For example, the attacker is able to modify any/all files protected by the vulnerable system. Alternatively, only some files can be modified, but malicious modification would present a direct, serious consequence to the vulnerable system.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Modification of data is possible, but the attacker does not have control over the consequence of a modification, or the amount of modification is limited. The data modification does not have a direct, serious impact to the Vulnerable System.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'There is no loss of integrity within the Vulnerable System.' 
    }] 
  },
  VA: {
    id: 'VA',
    name: 'Availability', 
    description: 'This metric measures the impact to the availability of the VULNERABLE SYSTEM resulting from a successfully exploited vulnerability. While the Confidentiality and Integrity impact metrics apply to the loss of confidentiality or integrity of data (e.g., information, files) used by the system, this metric refers to the loss of availability of the impacted system itself, such as a networked service (e.g., web, database, email). Since availability refers to the accessibility of information resources, attacks that consume network bandwidth, processor cycles, or disk space all impact the availability of a system.',
    choices: [{
      id: 'H',
      name: 'High', 
      description: 'There is a total loss of availability, resulting in the attacker being able to fully deny access to resources in the Vulnerable System; this loss is either sustained (while the attacker continues to deliver the attack) or persistent (the condition persists even after the attack has completed). Alternatively, the attacker has the ability to deny some availability, but the loss of availability presents a direct, serious consequence to the Vulnerable System (e.g., the attacker cannot disrupt existing connections, but can prevent new connections; the attacker can repeatedly exploit a vulnerability that, in each instance of a successful attack, leaks a only small amount of memory, but after repeated exploitation causes a service to become completely unavailable).' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Performance is reduced or there are interruptions in resource availability. Even if repeated exploitation of the vulnerability is possible, the attacker does not have the ability to completely deny service to legitimate users. The resources in the Vulnerable System are either partially available all of the time, or fully available only some of the time, but overall there is no direct, serious consequence to the Vulnerable System.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'There is no impact to availability within the Vulnerable System.' 
    }] 
  },
  SC: {
    id: 'SC',
    name: 'Confidentiality', 
    description: 'This metric measures the impact to the confidentiality of the information managed by the SUBSEQUENT SYSTEM due to a successfully exploited vulnerability. Confidentiality refers to limiting information access and disclosure to only authorized users, as well as preventing access by, or disclosure to, unauthorized ones.',
    choices: [{
      id: 'H',
      name: 'High', 
      description: "There is a total loss of confidentiality, resulting in all resources within the Subsequent System being divulged to the attacker. Alternatively, access to only some restricted information is obtained, but the disclosed information presents a direct, serious impact. For example, an attacker steals the administrator's password, or private encryption keys of a web server." 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'There is some loss of confidentiality. Access to some restricted information is obtained, but the attacker does not have control over what information is obtained, or the amount or kind of loss is limited. The information disclosure does not cause a direct, serious loss to the Subsequent System.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'There is no loss of confidentiality within the Subsequent System or all confidentiality impact is constrained to the Vulnerable System.' 
    }] 
  },
  SI: {
    id: 'SI',
    name: 'Integrity', 
    description: 'This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information. Integrity of the SUBSEQUENT SYSTEM is impacted when an attacker makes unauthorized modification of system data. Integrity is also impacted when a system user can repudiate critical actions taken in the context of the system (e.g. due to insufficient logging).',
    choices: [{
      id: 'H',
      name: 'High', 
      description: 'There is a total loss of integrity, or a complete loss of protection. For example, the attacker is able to modify any/all files protected by the Subsequent System. Alternatively, only some files can be modified, but malicious modification would present a direct, serious consequence to the Subsequent System.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Modification of data is possible, but the attacker does not have control over the consequence of a modification, or the amount of modification is limited. The data modification does not have a direct, serious impact to the Subsequent System.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'There is no loss of integrity within the Subsequent System or all integrity impact is constrained to the Vulnerable System.' 
    }] 
  },
  SA: {
    id: 'SA',
    name: 'Availability', 
    description: 'This metric measures the impact to the availability of the SUBSEQUENT SYSTEM resulting from a successfully exploited vulnerability. While the Confidentiality and Integrity impact metrics apply to the loss of confidentiality or integrity of data (e.g., information, files) used by the system, this metric refers to the loss of availability of the impacted system itself, such as a networked service (e.g., web, database, email). Since availability refers to the accessibility of information resources, attacks that consume network bandwidth, processor cycles, or disk space all impact the availability of a system.',
    choices: [{
      id: 'H',
      name: 'High', 
      description: 'There is a total loss of availability, resulting in the attacker being able to fully deny access to resources in the Subsequent System; this loss is either sustained (while the attacker continues to deliver the attack) or persistent (the condition persists even after the attack has completed). Alternatively, the attacker has the ability to deny some availability, but the loss of availability presents a direct, serious consequence to the Subsequent System (e.g., the attacker cannot disrupt existing connections, but can prevent new connections; the attacker can repeatedly exploit a vulnerability that, in each instance of a successful attack, leaks a only small amount of memory, but after repeated exploitation causes a service to become completely unavailable).' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Performance is reduced or there are interruptions in resource availability. Even if repeated exploitation of the vulnerability is possible, the attacker does not have the ability to completely deny service to legitimate users. The resources in the Subsequent System are either partially available all of the time, or fully available only some of the time, but overall there is no direct, serious consequence to the Subsequent System.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'There is no impact to availability within the Subsequent System or all availability impact is constrained to the Vulnerable System.' 
    }] 
  },
  S: {
    id: 'S',
    name: 'Safety', 
    description: 'When a system does have an intended use or fitness of purpose aligned to safety, it is possible that exploiting a vulnerability within that system may have Safety impact which can be represented in the Supplemental Metrics group. Lack of a Safety metric value being supplied does NOT mean that there may not be any Safety-related impacts.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'N',
      name: 'Negligible', 
      description: 'Consequences of the vulnerability meet definition of IEC 61508 consequence category "negligible."' 
    }, {
      id: 'P',
      name: 'Present', 
      description: 'Consequences of the vulnerability meet definition of IEC 61508 consequence categories of "marginal," "critical," or "catastrophic."' 
    }] 
  },
  AU: {
    id: 'AU',
    name: 'Automatable', 
    description: 'The “ The “Automatable” metric captures the answer to the question ”Can an attacker automate exploitation events for this vulnerability across multiple targets?” based on steps 1-4 of the kill chain [Hutchins et al., 2011]. These steps are reconnaissance, weaponization, delivery, and exploitation.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'N',
      name: 'No', 
      description: 'Attackers cannot reliably automate all 4 steps of the kill chain for this vulnerability for some reason. These steps are reconnaissance, weaponization, delivery, and exploitation.' 
    }, {
      id: 'Y',
      name: 'Yes', 
      description: 'Attackers can reliably automate all 4 steps of the kill chain. These steps are reconnaissance, weaponization, delivery, and exploitation (e.g., the vulnerability is “wormable”).' 
    }] 
  },
  R: {
    id: 'R',
    name: 'Recovery', 
    description: 'Recovery describes the resilience of a system to recover services, in terms of performance and availability, after an attack has been performed.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'A',
      name: 'Automatic', 
      description: 'The system recovers services automatically after an attack has been performed.' 
    }, {
      id: 'U',
      name: 'User', 
      description: 'The system requires manual intervention by the user to recover services, after an attack has been performed.' 
    }, {
      id: 'I',
      name: 'Irrecoverable', 
      description: 'The system services are irrecoverable by the user, after an attack has been performed.' 
    }] 
  },
  V: {
    id: 'V',
    name: 'Value Density', 
    description: 'Value Density describes the resources that the attacker will gain control over with a single exploitation event.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'D',
      name: 'Diffuse', 
      description: 'The vulnerable system has limited resources. That is, the resources that the attacker will gain control over with a single exploitation event are relatively small. An example of Diffuse (think: limited) Value Density would be an attack on a single email client vulnerability.' 
    }, {
      id: 'C',
      name: 'Concentrated', 
      description: 'The vulnerable system is rich in resources. Heuristically, such systems are often the direct responsibility of \\“system operators\\” rather than users. An example of Concentrated (think: broad) Value Density would be an attack on a central email server.' 
    }] 
  },
  RE: {
    id: 'RE',
    name: 'Vulnerability Response Effort', 
    description: 'The intention of the Vulnerability Response Effort metric is to provide supplemental information on how difficult it is for consumers to provide an initial response to the impact of vulnerabilities for deployed products and services in their infrastructure. The consumer can then take this additional information on effort required into consideration when applying mitigations and/or scheduling remediation.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'The effort required to respond to a vulnerability is low/trivial. Examples include: communication on better documentation, configuration workarounds, or guidance from the vendor that does not require an immediate update, upgrade, or replacement by the consuming entity, such as firewall filter configuration.' 
    }, {
      id: 'M',
      name: 'Moderate', 
      description: 'The actions required to respond to a vulnerability require some effort on behalf of the consumer and could cause minimal service impact to implement. Examples include: simple remote update, disabling of a subsystem, or a low-touch software upgrade such as a driver update.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'The actions required to respond to a vulnerability are significant and/or difficult, and may possibly lead to an extended, scheduled service impact.  This would need to be considered for scheduling purposes including honoring any embargo on deployment of the selected response. Alternatively, response to the vulnerability in the field is not possible remotely. The only resolution to the vulnerability involves physical replacement (e.g. units deployed would have to be recalled for a depot level repair or replacement). Examples include: a highly privileged driver update, microcode or UEFI BIOS updates, or software upgrades requiring careful analysis and understanding of any potential infrastructure impact before implementation. A UEFI BIOS update that impacts Trusted Platform Module (TPM) attestation without impacting disk encryption software such as Bit locker is a good recent example. Irreparable failures such as non-bootable flash subsystems, failed disks or solid-state drives (SSD), bad memory modules, network devices, or other non-recoverable under warranty hardware, should also be scored as having a High effort.' 
    }] 
  },
  U: {
    id: 'U',
    name: 'Provider Urgency', 
    description: 'To facilitate a standardized method to incorporate additional provider-supplied assessment, an optional “pass-through” Supplemental Metric called Provider Urgency is available. Note: While any assessment provider along the product supply chain may provide a Provider Urgency rating. The Penultimate Product Provider (PPP) is best positioned to provide a direct assessment of Provider Urgency.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'Clear',
      name: 'Clear', 
      description: 'Provider has assessed the impact of this vulnerability as having no urgency (Informational).' 
    }, {
      id: 'Green',
      name: 'Green', 
      description: 'Provider has assessed the impact of this vulnerability as having a reduced urgency.' 
    }, {
      id: 'Amber',
      name: 'Amber', 
      description: 'Provider has assessed the impact of this vulnerability as having a moderate urgency.' 
    }, {
      id: 'Red',
      name: 'Red', 
      description: 'Provider has assessed the impact of this vulnerability as having the highest urgency.' 
    }] 
  },
  MAV: {
    id: 'MAV',
    name: 'Attack Vector', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric reflects the context by which vulnerability exploitation is possible. This metric value (and consequently the resulting severity) will be larger the more remote (logically, and physically) an attacker can be in order to exploit the vulnerable system. The assumption is that the number of potential attackers for a vulnerability that could be exploited from across a network is larger than the number of potential attackers that could exploit a vulnerability requiring physical access to a device, and therefore warrants a greater severity.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'N',
      name: 'Network', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'A',
      name: 'Adjacent', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Local', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'P',
      name: 'Physical', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MAC: {
    id: 'MAC',
    name: 'Attack Complexity', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric captures measurable actions that must be taken by the attacker to actively evade or circumvent existing built-in security-enhancing conditions in order to obtain a working exploit. These are conditions whose primary purpose is to increase security and/or increase exploit engineering complexity. A vulnerability exploitable without a target-specific variable has a lower complexity than a vulnerability that would require non-trivial customization. This metric is meant to capture security mechanisms utilized by the vulnerable system.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MAT: {
    id: 'MAT',
    name: 'Attack Requirements', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric captures the prerequisite deployment and execution conditions or variables of the vulnerable system that enable the attack. These differ from security-enhancing techniques/technologies (ref Attack Complexity) as the primary purpose of these conditions is not to explicitly mitigate attacks, but rather, emerge naturally as a consequence of the deployment and execution of the vulnerable system.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'P',
      name: 'Present', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MPR: {
    id: 'MPR',
    name: 'Privileges Required', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric describes the level of privileges an attacker must possess prior to successfully exploiting the vulnerability. The method by which the attacker obtains privileged credentials prior to the attack (e.g., free trial accounts), is outside the scope of this metric. Generally, self-service provisioned accounts do not constitute a privilege requirement if the attacker can grant themselves privileges as part of the attack.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MUI: {
    id: 'MUI',
    name: 'User Interaction', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric captures the requirement for a human user, other than the attacker, to participate in the successful compromise of the vulnerable system. This metric determines whether the vulnerability can be exploited solely at the will of the attacker, or whether a separate user (or user-initiated process) must participate in some manner.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'P',
      name: 'Passive', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'A',
      name: 'Active', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MVC: {
    id: 'MVC',
    name: 'Confidentiality', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric measures the impact to the confidentiality of the information managed by the VULNERABLE SYSTEM due to a successfully exploited vulnerability. Confidentiality refers to limiting information access and disclosure to only authorized users, as well as preventing access by, or disclosure to, unauthorized ones.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MVI: {
    id: 'MVI',
    name: 'Integrity',
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information. Integrity of the VULNERABLE SYSTEM is impacted when an attacker makes unauthorized modification of system data. Integrity is also impacted when a system user can repudiate critical actions taken in the context of the system (e.g. due to insufficient logging).',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MVA: {
    id: 'MVA',
    name: 'Availability', 
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric measures the impact to the availability of the VULNERABLE SYSTEM resulting from a successfully exploited vulnerability. While the Confidentiality and Integrity impact metrics apply to the loss of confidentiality or integrity of data (e.g., information, files) used by the system, this metric refers to the loss of availability of the impacted system itself, such as a networked service (e.g., web, database, email). Since availability refers to the accessibility of information resources, attacks that consume network bandwidth, processor cycles, or disk space all impact the availability of a system.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'N',
      name: 'None', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MSC: {
    id: 'MSC',
    name: 'Confidentiality',
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric measures the impact to the confidentiality of the information managed by the SUBSEQUENT SYSTEM due to a successfully exploited vulnerability. Confidentiality refers to limiting information access and disclosure to only authorized users, as well as preventing access by, or disclosure to, unauthorized ones.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'N',
      name: 'Negligible', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MSI: {
    id: 'MSI',
    name: 'Integrity',
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information. Integrity of the SUBSEQUENT SYSTEM is impacted when an attacker makes unauthorized modification of system data. Integrity is also impacted when a system user can repudiate critical actions taken in the context of the system (e.g. due to insufficient logging). In addition to the logical systems defined for System of Interest, Subsequent Systems can also include impacts to humans.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'S',
      name: 'Safety', 
      description: 'The exploited vulnerability will result in integrity impacts that could cause serious injury or worse (categories of "Marginal" or worse as described in IEC 61508) to a human actor or participant.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'N',
      name: 'Negligible', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  MSA: {
    id: 'MSA',
    name: 'Availability',
    description: 'These metrics enable the consumer analyst to override individual Base metric values based on specific characteristics of a user’s environment. This metric measures the impact to the availability of the SUBSEQUENT SYSTEM resulting from a successfully exploited vulnerability. While the Confidentiality and Integrity impact metrics apply to the loss of confidentiality or integrity of data (e.g., information, files) used by the system, this metric refers to the loss of availability of the impacted system itself, such as a networked service (e.g., web, database, email). Since availability refers to the accessibility of information resources, attacks that consume network bandwidth, processor cycles, or disk space all impact the availability of a system. In addition to the logical systems defined for System of Interest, Subsequent Systems can also include impacts to humans.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The metric has not been evaluated.' 
    }, {
      id: 'S',
      name: 'Safety', 
      description: 'The exploited vulnerability will result in availability impacts that could cause serious injury or worse (categories of "Marginal" or worse as described in IEC 61508) to a human actor or participant.' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }, {
      id: 'N',
      name: 'Negligible', 
      description: 'This metric values has the same definition as the Base Metric value defined above.' 
    }] 
  },
  CR: {
    id: 'CR',
    name: 'Confidentiality Requirements', 
    description: 'This metric enables the consumer to customize the assessment depending on the importance of the affected IT asset to the analyst’s organization, measured in terms of Confidentiality. That is, if an IT asset supports a business function for which Confidentiality is most important, the analyst can assign a greater value to Confidentiality metrics relative to Integrity and Availability.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'Assigning this value indicates there is insufficient information to choose one of the other values, and has no impact on the overall Environmental Score' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'Loss of Confidentiality is likely to have a catastrophic adverse effect on the organization or individuals associated with the organization.' 
    }, {
      id: 'M',
      name: 'Medium', 
      description: 'Loss of Confidentiality is likely to have a serious adverse effect on the organization or individuals associated with the organization.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Loss of Confidentiality is likely to have only a limited adverse effect on the organization or individuals associated with the organization.' 
    }] 
  },
  IR: {
    id: 'IR',
    name: 'Integrity Requirements', 
    description: 'This metric enables the consumer to customize the assessment depending on the importance of the affected IT asset to the analyst’s organization, measured in terms of Integrity. That is, if an IT asset supports a business function for which Integrity is most important, the analyst can assign a greater value to Integrity metrics relative to Confidentiality and Availability.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'Assigning this value indicates there is insufficient information to choose one of the other values, and has no impact on the overall Environmental Score' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'Loss of Integrity is likely to have a catastrophic adverse effect on the organization or individuals associated with the organization.' 
    }, {
      id: 'M',
      name: 'Medium', 
      description: 'Loss of Integrity is likely to have a serious adverse effect on the organization or individuals associated with the organization.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Loss of Integrity is likely to have only a limited adverse effect on the organization or individuals associated with the organization.' 
    }] 
  },
  AR: {
    id: 'AR',
    name: 'Availability Requirements', 
    description: 'This metric enables the consumer to customize the assessment depending on the importance of the affected IT asset to the analyst’s organization, measured in terms of Availability. That is, if an IT asset supports a business function for which Availability is most important, the analyst can assign a greater value to Availability metrics relative to Confidentiality and Integrity.',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'Assigning this value indicates there is insufficient information to choose one of the other values, and has no impact on the overall Environmental Score' 
    }, {
      id: 'H',
      name: 'High', 
      description: 'Loss of Availability is likely to have a catastrophic adverse effect on the organization or individuals associated with the organization.' 
    }, {
      id: 'M',
      name: 'Medium', 
      description: 'Loss of Availability is likely to have a serious adverse effect on the organization or individuals associated with the organization.' 
    }, {
      id: 'L',
      name: 'Low', 
      description: 'Loss of Availability is likely to have only a limited adverse effect on the organization or individuals associated with the organization.' 
    }] 
  },
  E: {
    id: 'E',
    name: 'Exploit Maturity',
    description: 'This metric measures the likelihood of the vulnerability being attacked, and is typically based on the current state of exploit techniques, exploit code availability, or active, "in-the-wild" exploitation. It is the responsibility of the CVSS consumer to populate the values of Exploit Maturity (E) based on information regarding the availability of exploitation code/processes and the state of exploitation techniques. This information will be referred to as "threat intelligence".',
    choices: [{
      id: 'X',
      name: 'Not Defined', 
      description: 'The Exploit Maturity metric is not being used.  Reliable threat intelligence is not available to determine Exploit Maturity characteristics.' 
    }, {
      id: 'A',
      name: 'Attacked', 
      description: 'Based on threat intelligence sources either of the following must apply:\n· Attacks targeting this vulnerability (attempted or successful) have been reported\n· Solutions to simplify attempts to exploit the vulnerability are publicly or privately available (such as exploit toolkits)' 
    }, {
      id: 'P',
      name: 'POC', 
      description: 'Based on threat intelligence sources each of the following must apply:\n· Proof-of-concept is publicly available\n· No knowledge of reported attempts to exploit this vulnerability\n· No knowledge of publicly available solutions used to simplify attempts to exploit the vulnerability' 
    }, {
      id: 'U',
      name: 'Unreported', 
      description: 'Based on threat intelligence sources each of the following must apply:\n· No knowledge of publicly available proof-of-concept\n· No knowledge of reported attempts to exploit this vulnerability\n· No knowledge of publicly available solutions used to simplify attempts to exploit the vulnerability' 
    }
    ] 
  } 
});

const CVSS4_METRICS_BASE: CvssMetricsValueCollection = Object.freeze({
  AV: { N: 0.0, A: 0.1, L: 0.2, P: 0.3 },
  AC: { L: 0.0, H: 0.1 },
  AT: { N: 0.0, P: 0.1 },
  PR: { N: 0.0, L: 0.1, H: 0.2 },
  UI: { N: 0.0, P: 0.1, A: 0.2 },
  VC: { H: 0.0, L: 0.1, N: 0.2 },
  VI: { H: 0.0, L: 0.1, N: 0.2 },
  VA: { H: 0.0, L: 0.1, N: 0.2 },
  SC: { H: 0.1, L: 0.2, N: 0.3 },
  SI: { S: 0.0, H: 0.1, L: 0.2, N: 0.3 },
  SA: { S: 0.0, H: 0.1, L: 0.2, N: 0.3 },
})
const CVSS4_METRICS_THREAT: CvssMetricsValueCollection = Object.freeze({
  E: { X: 0, U: 0.2, P: 0.1, A: 0 },
})
const CVSS4_METRICS_ENVIRONMENTAL_REQUIREMENTS: CvssMetricsValueCollection = Object.freeze({
  CR: { X: null, H: 0.0, M: 0.1, L: 0.2 },
  IR: { X: null, H: 0.0, M: 0.1, L: 0.2 },
  AR: { X: null, H: 0.0, M: 0.1, L: 0.2 },
})
const CVSS4_METRICS_ENVIRONMENTAL_MODIFIED: CvssMetricsValueCollection = Object.freeze({
  MAV: { X: null, N: null, A: null, L: null, P: null },
  MAC: { X: null, L: null, H: null },
  MAT: { X: null, N: null, P: null },
  MPR: { X: null, N: null, L: null, H: null },
  MUI: { X: null, N: null, P: null, A: null },
  MVC: { X: null, H: null, L: null, N: null },
  MVI: { X: null, H: null, L: null, N: null },
  MVA: { X: null, H: null, L: null, N: null },
  MSC: { X: null, H: null, L: null, N: null },
  MSI: { X: null, S: null, H: null, L: null, N: null },
  MSA: { X: null, S: null, H: null, L: null, N: null },
})
const CVSS4_METRICS_ENVIRONMENTAL: CvssMetricsValueCollection = Object.freeze({ ...CVSS4_METRICS_ENVIRONMENTAL_REQUIREMENTS, ...CVSS4_METRICS_ENVIRONMENTAL_MODIFIED });
const CVSS4_METRICS_SUPPLEMENTAL: CvssMetricsValueCollection = Object.freeze({
  S: { X: null, N: null, P: null },
  AU: { X: null, N: null, Y: null },
  R: { X: null, A: null, U: null, I: null },
  V: { X: null, D: null, C: null },
  RE: { X: null, L: null, M: null, H: null },
  U: { X: null, Clear: null, Green: null, Amber: null, Red: null },
});
const CVSS4_METRICS = Object.freeze({
  ...CVSS4_METRICS_BASE,
  ...CVSS4_METRICS_THREAT,
  ...CVSS4_METRICS_ENVIRONMENTAL,
  ...CVSS4_METRICS_SUPPLEMENTAL
})

const CVSS4_LOOKUP_MACROVECTOR: { [key: string]: number } = Object.freeze({
  "000000": 10,
  "000001": 9.9,
  "000010": 9.8,
  "000011": 9.5,
  "000020": 9.5,
  "000021": 9.2,
  "000100": 10,
  "000101": 9.6,
  "000110": 9.3,
  "000111": 8.7,
  "000120": 9.1,
  "000121": 8.1,
  "000200": 9.3,
  "000201": 9,
  "000210": 8.9,
  "000211": 8,
  "000220": 8.1,
  "000221": 6.8,
  "001000": 9.8,
  "001001": 9.5,
  "001010": 9.5,
  "001011": 9.2,
  "001020": 9,
  "001021": 8.4,
  "001100": 9.3,
  "001101": 9.2,
  "001110": 8.9,
  "001111": 8.1,
  "001120": 8.1,
  "001121": 6.5,
  "001200": 8.8,
  "001201": 8,
  "001210": 7.8,
  "001211": 7,
  "001220": 6.9,
  "001221": 4.8,
  "002001": 9.2,
  "002011": 8.2,
  "002021": 7.2,
  "002101": 7.9,
  "002111": 6.9,
  "002121": 5,
  "002201": 6.9,
  "002211": 5.5,
  "002221": 2.7,
  "010000": 9.9,
  "010001": 9.7,
  "010010": 9.5,
  "010011": 9.2,
  "010020": 9.2,
  "010021": 8.5,
  "010100": 9.5,
  "010101": 9.1,
  "010110": 9,
  "010111": 8.3,
  "010120": 8.4,
  "010121": 7.1,
  "010200": 9.2,
  "010201": 8.1,
  "010210": 8.2,
  "010211": 7.1,
  "010220": 7.2,
  "010221": 5.3,
  "011000": 9.5,
  "011001": 9.3,
  "011010": 9.2,
  "011011": 8.5,
  "011020": 8.5,
  "011021": 7.3,
  "011100": 9.2,
  "011101": 8.2,
  "011110": 8,
  "011111": 7.2,
  "011120": 7,
  "011121": 5.9,
  "011200": 8.4,
  "011201": 7,
  "011210": 7.1,
  "011211": 5.2,
  "011220": 5,
  "011221": 3,
  "012001": 8.6,
  "012011": 7.5,
  "012021": 5.2,
  "012101": 7.1,
  "012111": 5.2,
  "012121": 2.9,
  "012201": 6.3,
  "012211": 2.9,
  "012221": 1.7,
  100000: 9.8,
  100001: 9.5,
  100010: 9.4,
  100011: 8.7,
  100020: 9.1,
  100021: 8.1,
  100100: 9.4,
  100101: 8.9,
  100110: 8.6,
  100111: 7.4,
  100120: 7.7,
  100121: 6.4,
  100200: 8.7,
  100201: 7.5,
  100210: 7.4,
  100211: 6.3,
  100220: 6.3,
  100221: 4.9,
  101000: 9.4,
  101001: 8.9,
  101010: 8.8,
  101011: 7.7,
  101020: 7.6,
  101021: 6.7,
  101100: 8.6,
  101101: 7.6,
  101110: 7.4,
  101111: 5.8,
  101120: 5.9,
  101121: 5,
  101200: 7.2,
  101201: 5.7,
  101210: 5.7,
  101211: 5.2,
  101220: 5.2,
  101221: 2.5,
  102001: 8.3,
  102011: 7,
  102021: 5.4,
  102101: 6.5,
  102111: 5.8,
  102121: 2.6,
  102201: 5.3,
  102211: 2.1,
  102221: 1.3,
  110000: 9.5,
  110001: 9,
  110010: 8.8,
  110011: 7.6,
  110020: 7.6,
  110021: 7,
  110100: 9,
  110101: 7.7,
  110110: 7.5,
  110111: 6.2,
  110120: 6.1,
  110121: 5.3,
  110200: 7.7,
  110201: 6.6,
  110210: 6.8,
  110211: 5.9,
  110220: 5.2,
  110221: 3,
  111000: 8.9,
  111001: 7.8,
  111010: 7.6,
  111011: 6.7,
  111020: 6.2,
  111021: 5.8,
  111100: 7.4,
  111101: 5.9,
  111110: 5.7,
  111111: 5.7,
  111120: 4.7,
  111121: 2.3,
  111200: 6.1,
  111201: 5.2,
  111210: 5.7,
  111211: 2.9,
  111220: 2.4,
  111221: 1.6,
  112001: 7.1,
  112011: 5.9,
  112021: 3,
  112101: 5.8,
  112111: 2.6,
  112121: 1.5,
  112201: 2.3,
  112211: 1.3,
  112221: 0.6,
  200000: 9.3,
  200001: 8.7,
  200010: 8.6,
  200011: 7.2,
  200020: 7.5,
  200021: 5.8,
  200100: 8.6,
  200101: 7.4,
  200110: 7.4,
  200111: 6.1,
  200120: 5.6,
  200121: 3.4,
  200200: 7,
  200201: 5.4,
  200210: 5.2,
  200211: 4,
  200220: 4,
  200221: 2.2,
  201000: 8.5,
  201001: 7.5,
  201010: 7.4,
  201011: 5.5,
  201020: 6.2,
  201021: 5.1,
  201100: 7.2,
  201101: 5.7,
  201110: 5.5,
  201111: 4.1,
  201120: 4.6,
  201121: 1.9,
  201200: 5.3,
  201201: 3.6,
  201210: 3.4,
  201211: 1.9,
  201220: 1.9,
  201221: 0.8,
  202001: 6.4,
  202011: 5.1,
  202021: 2,
  202101: 4.7,
  202111: 2.1,
  202121: 1.1,
  202201: 2.4,
  202211: 0.9,
  202221: 0.4,
  210000: 8.8,
  210001: 7.5,
  210010: 7.3,
  210011: 5.3,
  210020: 6,
  210021: 5,
  210100: 7.3,
  210101: 5.5,
  210110: 5.9,
  210111: 4,
  210120: 4.1,
  210121: 2,
  210200: 5.4,
  210201: 4.3,
  210210: 4.5,
  210211: 2.2,
  210220: 2,
  210221: 1.1,
  211000: 7.5,
  211001: 5.5,
  211010: 5.8,
  211011: 4.5,
  211020: 4,
  211021: 2.1,
  211100: 6.1,
  211101: 5.1,
  211110: 4.8,
  211111: 1.8,
  211120: 2,
  211121: 0.9,
  211200: 4.6,
  211201: 1.8,
  211210: 1.7,
  211211: 0.7,
  211220: 0.8,
  211221: 0.2,
  212001: 5.3,
  212011: 2.4,
  212021: 1.4,
  212101: 2.4,
  212111: 1.2,
  212121: 0.5,
  212201: 1,
  212211: 0.3,
  212221: 0.1,
})
const CVSS4_MAX_SEVERITY: { [key: string]: { [key: string]: number|any}} = Object.freeze({
  eq1: {
    0: 1,
    1: 4,
    2: 5
  },
  eq2: {
    0: 1,
    1: 2
  },
  eq3eq6: {
    0: { 0: 7, 1: 6 },
    1: { 0: 8, 1: 8 },
    2: { 1: 10 }
  },
  eq4: {
    0: 6,
    1: 5,
    2: 4
  },
  eq5: {
    0: 1,
    1: 1,
    2: 1
  },
});
const CVSS4_MAX_COMPOSED = Object.freeze({
  eq1: {
    0: ["AV:N/PR:N/UI:N/"],
    1: ["AV:A/PR:N/UI:N/", "AV:N/PR:L/UI:N/", "AV:N/PR:N/UI:P/"],
    2: ["AV:P/PR:N/UI:N/", "AV:A/PR:L/UI:P/"]
  },
  eq2: {
    0: ["AC:L/AT:N/"],
    1: ["AC:H/AT:N/", "AC:L/AT:P/"]
  },
  eq3: {
    0: { 0: ["VC:H/VI:H/VA:H/CR:H/IR:H/AR:H/"], 1: ["VC:H/VI:H/VA:L/CR:M/IR:M/AR:H/", "VC:H/VI:H/VA:H/CR:M/IR:M/AR:M/"] },
    1: { 0: ["VC:L/VI:H/VA:H/CR:H/IR:H/AR:H/", "VC:H/VI:L/VA:H/CR:H/IR:H/AR:H/"], 1: ["VC:L/VI:H/VA:L/CR:H/IR:M/AR:H/", "VC:L/VI:H/VA:H/CR:H/IR:M/AR:M/", "VC:H/VI:L/VA:H/CR:M/IR:H/AR:M/", "VC:H/VI:L/VA:L/CR:M/IR:H/AR:H/", "VC:L/VI:L/VA:H/CR:H/IR:H/AR:M/"] },
    2: { 1: ["VC:L/VI:L/VA:L/CR:H/IR:H/AR:H/"] },
  },
  eq4: {
    0: ["SC:H/SI:S/SA:S/"],
    1: ["SC:H/SI:H/SA:H/"],
    2: ["SC:L/SI:L/SA:L/"]

  },
  eq5: {
    0: ["E:A/"],
    1: ["E:P/"],
    2: ["E:U/"],
  },
}) as { [key: string]: { [key: number]: string[]|any } };

export function parseVectorCvss4(vector?: string|null): CvssMetricsValue {
  // Vector to string
  const out = {} as CvssMetricsValue;
  for (const part of (vector || '').slice(9).split('/')) {
    const kv = part.split(':');
    out[kv[0]] = kv.length > 1 ? kv[1] : null;
  }

  // Set undefined metrics
  for (const m of Object.keys(CVSS4_METRICS)) {
    if (!(m in out)) {
      out[m] = 'X';
    }
  }

  return out;
}

export function isValidVectorCvss4(vector?: string|null) {
  // Check CVSS identifier
  if (!vector || !vector.startsWith('CVSS:4.0/')) {
    return false;
  }

  const parsedVector = parseVectorCvss4(vector) || {};

  // Only allowed values defined
  for (const [k, v] of Object.entries(parsedVector)) {
    if (!(k in CVSS4_METRICS && v in CVSS4_METRICS[k])) {
      return false;
    }
  }

  // all base metrics defined
  for (const m of Object.keys(CVSS4_METRICS_BASE)) {
    if (!(m in parsedVector)) {
      return false;
    }
  }

  return true;
}

export function stringifyVectorCvss40(parsedVector: CvssMetricsValue): string {
  let out = CvssVersion.CVSS40 as string;
  for (const [k, vs] of Object.entries(CVSS4_METRICS)) {
    if (k in parsedVector && parsedVector[k] in vs && parsedVector[k] !== 'X') {
      out += `/${k}:${parsedVector[k]}`;
    }
  }
  return out;
}

function eqsToMacroVector(eq1: number, eq2: number, eq3: number, eq4: number, eq5: number, eq6: number) {
  return `${eq1}${eq2}${eq3}${eq4}${eq5}${eq6}`;
}

function extractValueMetric(name: string, maxVector: string) {
  // indexOf gives first index of the metric, we then need to go over its size
  const extracted = maxVector.slice(maxVector.indexOf(name) + name.length + 1)
  // remove what follow
  let metricVal = extracted;
  if (extracted.indexOf('/') > 0) {
    metricVal = extracted.substring(0, extracted.indexOf('/'));
  }
  return metricVal;
}

function getEqMaxes(lookup: string, eq: number) {
  return CVSS4_MAX_COMPOSED[`eq${eq}`][Number.parseInt(lookup[eq - 1])];
}

export function calculateScoreCvss40(vector?: string|null): number|null {
  if (!isValidVectorCvss4(vector)) {
    return null;
  }
  const values = parseVectorCvss4(vector);

  function metric(name: string): string {
    const m = values[name] || 'X';
    const modifiedFallback = {
      E: 'A',
      CR: 'H',
      IR: 'H',
      AR: 'H',
    } as { [key: string]: string };
    if (name in modifiedFallback && m === 'X') {
      return modifiedFallback[name];
    } else if (values['M' + name] && values['M' + name] !== 'X') {
      return values['M' + name];
    }
    return m;
  }

  function calculateMacroVector() {
    const eq1 = (metric('AV') === 'N' && metric('PR') === 'N' && metric('UI') === 'N') ? 0 :
        ((metric('AV') === 'N' || metric('PR') === 'N' || metric('UI') === 'N') && !(metric('AV') === 'N' && metric('PR') === 'N' && metric('UI') === 'N') && !(metric('AV') === 'P')) ? 1 :
            (metric('AV') === 'P' || !(metric('AV') === 'N' || metric('PR') === 'N' || metric('UI') === 'N')) ? 2 : 
              Number.NaN;
    const eq2 = (metric('AC') === 'L' && metric('AT') === 'N') ? 0 :
        !(metric('AC') === 'L' && metric('AT') === 'N') ? 1 :
          Number.NaN;
    const eq3 = (metric('VC') === 'H' && metric('VI') === 'H') ? 0 :
        (!(metric('VC') === 'H' && metric('VI') === 'H') && (metric('VC') === 'H' || metric('VI') === 'H' || metric('VA') === 'H')) ? 1 :
            !(metric('VC') === 'H' || metric('VI') === 'H' || metric('VA') === 'H') ? 2 :
              Number.NaN;
    const eq4 = (metric('MSI') === 'S' || metric('MSA') === 'S') ? 0 :
        !(metric('MSI') === 'S' || metric('MSA') === 'S') && (metric('SC') === 'H' || metric('SI') === 'H' || metric('SA') === 'H') ? 1 :
            !(metric('MSI') === 'S' || metric('MSA') === 'S') && !(metric('SC') === 'H' || metric('SI') === 'H' || metric('SA') === 'H') ? 2 :
              Number.NaN;
    const eq5 = (metric('E') === 'A') ? 0 :
        (metric('E') === 'P') ? 1 :
            (metric('E') === 'U') ? 2 :
              Number.NaN;
    const eq6 = ((metric('CR') === 'H' && metric('VC') === 'H') || (metric('IR') === 'H' && metric('VI') === 'H') || (metric('AR') === 'H' && metric('VA') === 'H')) ? 0 :
        !((metric('CR') === 'H' && metric('VC') === 'H') || (metric('IR') === 'H' && metric('VI') === 'H') || (metric('AR') === 'H' && metric('VA') === 'H')) ? 1 :
          Number.NaN;
    return { eq1, eq2, eq3, eq4, eq5, eq6 };
  }

  // Exception for no impact on system (shortcut)
  if (['VC', 'VI', 'VA', 'SC', 'SI', 'SA'].every(m => metric(m) === 'N')) {
    return 0.0;
  }

  const { eq1, eq2, eq3, eq4, eq5, eq6 } = calculateMacroVector();
  const macroVector = eqsToMacroVector(eq1, eq2, eq3, eq4, eq5, eq6);
  const value = CVSS4_LOOKUP_MACROVECTOR[macroVector];

  // 1. For each of the EQs:
  //   a. The maximal scoring difference is determined as the difference
  //      between the current MacroVector and the lower MacroVector.
  //     i. If there is no lower MacroVector the available distance is
  //        set to NaN and then ignored in the further calculations.

  // compute next lower macro, it can also not exist
  const eq1_next_lower_macro = eqsToMacroVector(eq1 + 1, eq2, eq3, eq4, eq5, eq6);
  const eq2_next_lower_macro = eqsToMacroVector(eq1, eq2 + 1, eq3, eq4, eq5, eq6);

  // eq3 and eq6 are relateqs_to_macrovector
  let eq3eq6_next_lower_macro = '';
  let eq3eq6_next_lower_macro_left = '';
  let eq3eq6_next_lower_macro_right = '';
  if ((eq3 === 1 && eq6 === 1) || (eq3 === 0 && eq6 === 1)) {
    // 11 --> 21
    // 01 --> 11
    eq3eq6_next_lower_macro = eqsToMacroVector(eq1, eq2, eq3 + 1, eq4, eq5, eq6)
  } else if (eq3 === 1 && eq6 === 0) {
    // 10 --> 11
    eq3eq6_next_lower_macro = eqsToMacroVector(eq1, eq2, eq3, eq4, eq5, eq6 + 1)
  } else if (eq3 === 0 && eq6 === 0) {
    // 00 --> 01
    // 00 --> 10
    eq3eq6_next_lower_macro_left = eqsToMacroVector(eq1, eq2, eq3, eq4, eq5, eq6 + 1)
    eq3eq6_next_lower_macro_right = eqsToMacroVector(eq1, eq2, eq3 + 1, eq4, eq5, eq6)
  } else {
    // 21 --> 32 (do not exist)
    eq3eq6_next_lower_macro = eqsToMacroVector(eq1, eq2, eq3 + 1, eq4, eq5, eq6 + 1)
  }
  const eq4_next_lower_macro = eqsToMacroVector(eq1, eq2, eq3, eq4 + 1, eq5, eq6)
  const eq5_next_lower_macro = eqsToMacroVector(eq1, eq2, eq3, eq4, eq5 + 1, eq6)

  // get their score, if the next lower macro score do not exist the result is NaN
  const score_eq1_next_lower_macro = CVSS4_LOOKUP_MACROVECTOR[eq1_next_lower_macro];
  const score_eq2_next_lower_macro = CVSS4_LOOKUP_MACROVECTOR[eq2_next_lower_macro];

  let score_eq3eq6_next_lower_macro = 0;
  if (eq3 === 0 && eq6 === 0) {
    // multiple path take the one with higher score
    const score_eq3eq6_next_lower_macro_left = CVSS4_LOOKUP_MACROVECTOR[eq3eq6_next_lower_macro_left];
    const score_eq3eq6_next_lower_macro_right = CVSS4_LOOKUP_MACROVECTOR[eq3eq6_next_lower_macro_right];
    if (score_eq3eq6_next_lower_macro_left > score_eq3eq6_next_lower_macro_right) {
      score_eq3eq6_next_lower_macro = score_eq3eq6_next_lower_macro_left
    } else {
      score_eq3eq6_next_lower_macro = score_eq3eq6_next_lower_macro_right
    } 
  } else {
    score_eq3eq6_next_lower_macro = CVSS4_LOOKUP_MACROVECTOR[eq3eq6_next_lower_macro]
  }

  const score_eq4_next_lower_macro = CVSS4_LOOKUP_MACROVECTOR[eq4_next_lower_macro]
  const score_eq5_next_lower_macro = CVSS4_LOOKUP_MACROVECTOR[eq5_next_lower_macro]

  //   b. The severity distance of the to-be scored vector from a
  //      highest severity vector in the same MacroVector is determined.
  const eq1_maxes = getEqMaxes(macroVector, 1)
  const eq2_maxes = getEqMaxes(macroVector, 2)
  const eq3_eq6_maxes = getEqMaxes(macroVector, 3)[macroVector[5]]
  const eq4_maxes = getEqMaxes(macroVector, 4)
  const eq5_maxes = getEqMaxes(macroVector, 5)

  const max_vectors = [] as string[];
  for (const eq1_max of eq1_maxes) {
    for (const eq2_max of eq2_maxes) {
      for (const eq3_eq6_max of eq3_eq6_maxes) {
        for (const eq4_max of eq4_maxes) {
          for (const eq5max of eq5_maxes) {
            max_vectors.push(eq1_max + eq2_max + eq3_eq6_max + eq4_max + eq5max)
          }
        }
      }
    }
  }

  // Find the max vector to use i.e. one in the combination of all the highests
  // that is greater or equal (severity distance) than the to-be scored vector.
  const severity_distances = {} as { [key: string]: number };
  for (const max_vector of max_vectors) {
    for (const m of [...Object.keys(CVSS4_METRICS_BASE), ...Object.keys(CVSS4_METRICS_THREAT), ...Object.keys(CVSS4_METRICS_ENVIRONMENTAL_REQUIREMENTS)]) {
      severity_distances[m] = CVSS4_METRICS[m][metric(m)] - CVSS4_METRICS[m][extractValueMetric(m, max_vector)]
    }
    // if any is less than zero this is not the right max
    if (Object.values(severity_distances).some(m => m < 0)) {
      continue;
    }
    // if multiple maxes exist to reach it it is enough the first one
    break
  }

  const current_severity_distance_eq1 = severity_distances.AV + severity_distances.PR + severity_distances.UI
  const current_severity_distance_eq2 = severity_distances.AC + severity_distances.AT
  const current_severity_distance_eq3eq6 = severity_distances.VC + severity_distances.VI + severity_distances.VA + severity_distances.CR + severity_distances.IR + severity_distances.AR
  const current_severity_distance_eq4 = severity_distances.SC + severity_distances.SI + severity_distances.SA
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const current_severity_distance_eq5 = 0

  const step = 0.1

  // if the next lower macro score do not exist the result is Nan
  // Rename to maximal scoring difference (aka MSD)
  const available_distance_eq1 = value - score_eq1_next_lower_macro
  const available_distance_eq2 = value - score_eq2_next_lower_macro
  const available_distance_eq3eq6 = value - score_eq3eq6_next_lower_macro
  const available_distance_eq4 = value - score_eq4_next_lower_macro
  const available_distance_eq5 = value - score_eq5_next_lower_macro

  let percent_to_next_eq1_severity = 0
  let percent_to_next_eq2_severity = 0
  let percent_to_next_eq3eq6_severity = 0
  let percent_to_next_eq4_severity = 0
  let percent_to_next_eq5_severity = 0

  // some of them do not exist, we will find them by retrieving the score. If score null then do not exist
  let n_existing_lower = 0

  let normalized_severity_eq1 = 0
  let normalized_severity_eq2 = 0
  let normalized_severity_eq3eq6 = 0
  let normalized_severity_eq4 = 0
  let normalized_severity_eq5 = 0

  // multiply by step because distance is pure
  const max_severity_eq1 = CVSS4_MAX_SEVERITY.eq1[eq1] * step
  const max_severity_eq2 = CVSS4_MAX_SEVERITY.eq2[eq2] * step
  const max_severity_eq3eq6 = CVSS4_MAX_SEVERITY.eq3eq6[eq3][eq6] * step
  const max_severity_eq4 = CVSS4_MAX_SEVERITY.eq4[eq4] * step
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const max_severity_eq5 = CVSS4_MAX_SEVERITY.eq5[eq5] * step

  //   c. The proportion of the distance is determined by dividing
  //      the severity distance of the to-be-scored vector by the depth
  //      of the MacroVector.
  //   d. The maximal scoring difference is multiplied by the proportion of
  //      distance.
  if (!Number.isNaN(available_distance_eq1)) {
    n_existing_lower += 1
    percent_to_next_eq1_severity = current_severity_distance_eq1 / max_severity_eq1
    normalized_severity_eq1 = available_distance_eq1 * percent_to_next_eq1_severity
  }
  if (!Number.isNaN(available_distance_eq2)) {
    n_existing_lower += 1
    percent_to_next_eq2_severity = current_severity_distance_eq2 / max_severity_eq2
    normalized_severity_eq2 = available_distance_eq2 * percent_to_next_eq2_severity
  }
  if (!Number.isNaN(available_distance_eq3eq6)) {
    n_existing_lower += 1
    percent_to_next_eq3eq6_severity = current_severity_distance_eq3eq6 / max_severity_eq3eq6
    normalized_severity_eq3eq6 = available_distance_eq3eq6 * percent_to_next_eq3eq6_severity
  } if (!Number.isNaN(available_distance_eq4)) {
    n_existing_lower += 1
    percent_to_next_eq4_severity = current_severity_distance_eq4 / max_severity_eq4
    normalized_severity_eq4 = available_distance_eq4 * percent_to_next_eq4_severity
  }
  if (!Number.isNaN(available_distance_eq5)) {
    // for eq5 is always 0 the percentage
    n_existing_lower += 1
    percent_to_next_eq5_severity = 0
    normalized_severity_eq5 = available_distance_eq5 * percent_to_next_eq5_severity
  }

  // 2. The mean of the above computed proportional distances is computed.
  let mean_distance = 0
  if (n_existing_lower !== 0) {
    mean_distance = (normalized_severity_eq1 + normalized_severity_eq2 + normalized_severity_eq3eq6 + normalized_severity_eq4 + normalized_severity_eq5) / n_existing_lower
  }

  const score = Math.min(Math.max(value - mean_distance, 0.0), 10.0);
  return Number(score.toFixed(1));
}
