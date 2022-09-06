export const CVSS31_DEFINITION = Object.freeze({
  AV: {
    id: "AV",
    name: "Attack Vector",
    description: "This metric reflects the context by which vulnerability exploitation is possible. The Base Score increases the more remote (logically, and physically) an attacker can be in order to exploit the vulnerable component.",
    choices: [
      {
        id: "N",
        name: "Network",
        description: "A vulnerability exploitable with network access means the vulnerable component is bound to the network stack and the attacker's path is through OSI layer 3 (the network layer). Such a vulnerability is often termed \"remotely exploitable” and can be thought of as an attack being exploitable one or more network hops away."
      },
      {
        id: "A",
        name: "Adjacent",
        description: "A vulnerability exploitable with adjacent network access means the vulnerable component is bound to the network stack, however the attack is limited to the same shared physical (e.g. Bluetooth, IEEE 802.11), or logical (e.g. local IP subnet) network, and cannot be performed across an OSI layer 3 boundary (e.g. a router)."
      },
      {
        id: "L",
        name: "Local",
        description: "A vulnerability exploitable with local access means that the vulnerable component is not bound to the network stack, and the attacker’s path is via read/write/execute capabilities. In some cases, the attacker may be logged in locally in order to exploit the vulnerability, otherwise, she may rely on User Interaction to execute a malicious file."
      },
      {
        id: "P",
        name: "Physical",
        description: "A vulnerability exploitable with physical access requires the attacker to physically touch or manipulate the vulnerable component. Physical interaction may be brief or persistent."
      }
    ]
  },
  AC: {
    id: "AC",
    name: "Attack Complexity",
    description: "This metric describes the conditions beyond the attacker’s control that must exist in order to exploit the vulnerability. Such conditions may require the collection of more information about the target, the presence of certain system configuration settings, or computational exceptions.",
    choices: [
      {
        id: "L",
        name: "Low",
        description: "Specialized access conditions or extenuating circumstances do not exist. An attacker can expect repeatable success against the vulnerable component."
      },
      {
        id: "H",
        name: "High",
        description: "A successful attack depends on conditions beyond the attacker's control. That is, a successful attack cannot be accomplished at will, but requires the attacker to invest in some measurable amount of effort in preparation or execution against the vulnerable component before a successful attack can be expected. For example, a successful attack may require the attacker: to perform target-specific reconnaissance; to prepare the target environment to improve exploit reliability; or to inject herself into the logical network path between the target and the resource requested by the victim in order to read and/or modify network communications (e.g. a man in the middle attack)."
      }
    ]
  },
  PR: {
    id: "PR",
    name: "Privileges Required",
    description: "This metric describes the level of privileges an attacker must possess before successfully exploiting the vulnerability. This Base Score increases as fewer privileges are required.",
    choices: [
      {
        id: "N",
        name: "None",
        description: "The attacker is unauthorized prior to attack, and therefore does not require any access to settings or files to carry out an attack."
      },
      {
        id: "L",
        name: "Low",
        description: "The attacker is authorized with (i.e. requires) privileges that provide basic user capabilities that could normally affect only settings and files owned by a user. Alternatively, an attacker with Low privileges may have the ability to cause an impact only to non-sensitive resources."
      },
      {
        id: "H",
        name: "High",
        description: "The attacker is authorized with (i.e. requires) privileges that provide significant (e.g. administrative) control over the vulnerable component that could affect component-wide settings and files."
      }
    ]
  },
  UI: {
    id: "UI",
    name: "User Interaction",
    description: "This metric captures the requirement for a user, other than the attacker, to participate in the successful compromise the vulnerable component. This metric determines whether the vulnerability can be exploited solely at the will of the attacker, or whether a separate user (or user-initiated process) must participate in some manner. The Base Score is highest when no user interaction is required.",
    choices: [
      {
        id: "N",
        name: "None",
        description: "The vulnerable system can be exploited without any interaction from any user."
      },
      {
        id: "R",
        name: "Required",
        description: "Successful exploitation of this vulnerability requires a user to take some action before the vulnerability can be exploited."
      }
    ]
  },
  S: {
    id: "S",
    name: "Scope",
    description: "Does a successful attack impact a component other than the vulnerable component? If so, the Base Score increases and the Confidentiality, Integrity and Authentication metrics should be scored relative to the impacted component.",
    choices: [
      {
        id: "U",
        name: "Unchanged",
        description: "An exploited vulnerability can only affect resources managed by the same authority. In this case the vulnerable component and the impacted component are the same."
      },
      {
        id: "C",
        name: "Changed",
        description: "An exploited vulnerability can affect resources beyond the authorization privileges intended by the vulnerable component. In this case the vulnerable component and the impacted component are different."
      }
    ]
  },
  C: {
    id: "C",
    name: "Confidentiality",
    description: "This metric measures the impact to the confidentiality of the information resources managed by a software component due to a successfully exploited vulnerability. Confidentiality refers to limiting information access and disclosure to only authorized users, as well as preventing access by, or disclosure to, unauthorized ones.",
    choices: [
      {
        id: "N",
        name: "None",
        description: "There is no loss of confidentiality within the impacted component."
      },
      {
        id: "L",
        name: "Low",
        description: "There is some loss of confidentiality. Access to some restricted information is obtained, but the attacker does not have control over what information is obtained, or the amount or kind of loss is constrained. The information disclosure does not cause a direct, serious loss to the impacted component."
      },
      {
        id: "H",
        name: "High",
        description: "There is total loss of confidentiality, resulting in all resources within the impacted component being divulged to the attacker. Alternatively, access to only some restricted information is obtained, but the disclosed information presents a direct, serious impact."
      }
    ]
  },
  I: {
    id: "I",
    name: "Integrity",
    description: "This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information.",
    choices: [
      {
        id: "N",
        name: "None",
        description: "There is no loss of integrity within the impacted component."
      },
      {
        id: "L",
        name: "Low",
        description: "Modification of data is possible, but the attacker does not have control over the consequence of a modification, or the amount of modification is constrained. The data modification does not have a direct, serious impact on the impacted component."
      },
      {
        id: "H",
        name: "High",
        description: "There is a total loss of integrity, or a complete loss of protection. For example, the attacker is able to modify any/all files protected by the impacted component. Alternatively, only some files can be modified, but malicious modification would present a direct, serious consequence to the impacted component."
      }
    ]
  },
  A: {
    id: "A",
    name: "Availability",
    description: "This metric measures the impact to the availability of the impacted component resulting from a successfully exploited vulnerability. It refers to the loss of availability of the impacted component itself, such as a networked service (e.g., web, database, email). Since availability refers to the accessibility of information resources, attacks that consume network bandwidth, processor cycles, or disk space all impact the availability of an impacted component.",
    choices: [
      {
        id: "N",
        name: "None",
        description: "There is no impact to availability within the impacted component."
      },
      {
        id: "L",
        name: "Low",
        description: "There is reduced performance or interruptions in resource availability. Even if repeated exploitation of the vulnerability is possible, the attacker does not have the ability to completely deny service to legitimate users. The resources in the impacted component are either partially available all of the time, or fully available only some of the time, but overall there is no direct, serious consequence to the impacted component."
      },
      {
        id: "H",
        name: "High",
        description: "There is total loss of availability, resulting in the attacker being able to fully deny access to resources in the impacted component; this loss is either sustained (while the attacker continues to deliver the attack) or persistent (the condition persists even after the attack has completed). Alternatively, the attacker has the ability to deny some availability, but the loss of availability presents a direct, serious consequence to the impacted component (e.g., the attacker cannot disrupt existing connections, but can prevent new connections; the attacker can repeatedly exploit a vulnerability that, in each instance of a successful attack, leaks a only small amount of memory, but after repeated exploitation causes a service to become completely unavailable)."
      }
    ]
  },
  E: {
    id: "E",
    name: "Exploit Code Maturity",
    description: "This metric measures the likelihood of the vulnerability being attacked, and is typically based on the current state of exploit techniques, exploit code availability, or active, 'in-the-wild' exploitation.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "U",
        name: "Unproven",
        description: "No exploit code is available, or an exploit is theoretical."
      },
      {
        id: "P",
        name: "Proof-of-Concept",
        description: "Proof-of-concept exploit code is available, or an attack demonstration is not practical for most systems. The code or technique is not functional in all situations and may require substantial modification by a skilled attacker."
      },
      {
        id: "F",
        name: "Functional",
        description: "Functional exploit code is available. The code works in most situations where the vulnerability exists."
      },
      {
        id: "H",
        name: "High",
        description: "Functional autonomous code exists, or no exploit is required (manual trigger) and details are widely available. Exploit code works in every situation, or is actively being delivered via an autonomous agent (such as a worm or virus). Network-connected systems are likely to encounter scanning or exploitation attempts. Exploit development has reached the level of reliable, widely-available, easy-to-use automated tools."
      }
    ]
  },
  RL: {
    id: "RL",
    name: "Remediation Level",
    description: "The Remediation Level of a vulnerability is an important factor for prioritization. The typical vulnerability is unpatched when initially published. Workarounds or hotfixes may offer interim remediation until an official patch or upgrade is issued. Each of these respective stages adjusts the temporal score downwards, reflecting the decreasing urgency as remediation becomes final.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "O",
        name: "Official Fix",
        description: "A complete vendor solution is available. Either the vendor has issued an official patch, or an upgrade is available."
      },
      {
        id: "T",
        name: "Temporary Fix",
        description: "There is an official but temporary fix available. This includes instances where the vendor issues a temporary hotfix, tool, or workaround."
      },
      {
        id: "W",
        name: "Workaround",
        description: "There is an unofficial, non-vendor solution available. In some cases, users of the affected technology will create a patch of their own or provide steps to work around or otherwise mitigate the vulnerability."
      },
      {
        id: "U",
        name: "Unavailable",
        description: "There is either no solution available or it is impossible to apply."
      }
    ]
  },
  RC: {
    id: "RC",
    name: "Report Confidence",
    description: "This metric measures the degree of confidence in the existence of the vulnerability and the credibility of the known technical details. Sometimes only the existence of vulnerabilities are publicized, but without specific details. For example, an impact may be recognized as undesirable, but the root cause may not be known. The vulnerability may later be corroborated by research which suggests where the vulnerability may lie, though the research may not be certain. Finally, a vulnerability may be confirmed through acknowledgement by the author or vendor of the affected technology. The urgency of a vulnerability is higher when a vulnerability is known to exist with certainty. This metric also suggests the level of technical knowledge available to would-be attackers.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "U",
        name: "Unknown",
        description: "There are reports of impacts that indicate a vulnerability is present. The reports indicate that the cause of the vulnerability is unknown, or reports may differ on the cause or impacts of the vulnerability. Reporters are uncertain of the true nature of the vulnerability, and there is little confidence in the validity of the reports or whether a static Base score can be applied given the differences described. An example is a bug report which notes that an intermittent but non-reproducible crash occurs, with evidence of memory corruption suggesting that denial of service, or possible more serious impacts, may result."
      },
      {
        id: "R",
        name: "Reasonable",
        description: "Significant details are published, but researchers either do not have full confidence in the root cause, or do not have access to source code to fully confirm all of the interactions that may lead to the result. Reasonable confidence exists, however, that the bug is reproducible and at least one impact is able to be verified (Proof-of-concept exploits may provide this). An example is a detailed write-up of research into a vulnerability with an explanation (possibly obfuscated or 'left as an exercise to the reader') that gives assurances on how to reproduce the results."
      },
      {
        id: "C",
        name: "Confirmed",
        description: "Detailed reports exist, or functional reproduction is possible (functional exploits may provide this). Source code is available to independently verify the assertions of the research, or the author or vendor of the affected code has confirmed the presence of the vulnerability."
      }
    ]
  },
  CR: {
    id: "CR",
    name: "Confidentiality Requirement",
    description: "These metrics enable the analyst to customize the CVSS score depending on the importance of the Confidentiality of the affected IT asset to a user’s organization, relative to other impacts. This metric modifies the environmental score by reweighting the Modified Confidentiality impact metric versus the other modified impacts.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "L",
        name: "Low",
        description: "Loss of Confidentiality is likely to have only a limited adverse effect on the organization or individuals associated with the organization (e.g., employees, customers)."
      },
      {
        id: "M",
        name: "Medium",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "H",
        name: "High",
        description: "Loss of Confidentiality is likely to have a catastrophic adverse effect on the organization or individuals associated with the organization (e.g., employees, customers)."
      }
    ]
  },
  IR: {
    id: "IR",
    name: "Integrity Requirement",
    description: "These metrics enable the analyst to customize the CVSS score depending on the importance of the Integrity of the affected IT asset to a user’s organization, relative to other impacts. This metric modifies the environmental score by reweighting the Modified Integrity impact metric versus the other modified impacts.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "L",
        name: "Low",
        description: "Loss of Integrity is likely to have only a limited adverse effect on the organization or individuals associated with the organization (e.g., employees, customers)."
      },
      {
        id: "M",
        name: "Medium",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "H",
        name: "High",
        description: "Loss of Integrity is likely to have a catastrophic adverse effect on the organization or individuals associated with the organization (e.g., employees, customers)."
      }
    ]
  },
  AR: {
    id: "AR",
    name: "Availability Requirement",
    description: "These metrics enable the analyst to customize the CVSS score depending on the importance of the Availability of the affected IT asset to a user’s organization, relative to other impacts. This metric modifies the environmental score by reweighting the Modified Availability impact metric versus the other modified impacts.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "L",
        name: "Low",
        description: "Loss of Availability is likely to have only a limited adverse effect on the organization or individuals associated with the organization (e.g., employees, customers)."
      },
      {
        id: "M",
        name: "Medium",
        description: "Assigning this value to the metric will not influence the score."
      },
      {
        id: "H",
        name: "High",
        description: "Loss of Availability is likely to have a catastrophic adverse effect on the organization or individuals associated with the organization (e.g., employees, customers)."
      }
    ]
  },
  MAV: {
    id: "MAV",
    name: "Modified Attack Vector",
    description: "This metric reflects the context by which vulnerability exploitation is possible. The Base Score increases the more remote (logically, and physically) an attacker can be in order to exploit the vulnerable component.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "N",
        name: "Network",
        description: "A vulnerability exploitable with network access means the vulnerable component is bound to the network stack and the attacker's path is through OSI layer 3 (the network layer). Such a vulnerability is often termed \"remotely exploitable” and can be thought of as an attack being exploitable one or more network hops away."
      },
      {
        id: "A",
        name: "Adjacent Network",
        description: "A vulnerability exploitable with adjacent network access means the vulnerable component is bound to the network stack, however the attack is limited to the same shared physical (e.g. Bluetooth, IEEE 802.11), or logical (e.g. local IP subnet) network, and cannot be performed across an OSI layer 3 boundary (e.g. a router)."
      },
      {
        id: "L",
        name: "Local",
        description: "A vulnerability exploitable with local access means that the vulnerable component is not bound to the network stack, and the attacker’s path is via read/write/execute capabilities. In some cases, the attacker may be logged in locally in order to exploit the vulnerability, otherwise, she may rely on User Interaction to execute a malicious file."
      },
      {
        id: "P",
        name: "Physical",
        description: "A vulnerability exploitable with physical access requires the attacker to physically touch or manipulate the vulnerable component. Physical interaction may be brief or persistent."
      }
    ]
  },
  MAC: {
    id: "MAC",
    name: "Modified Attack Complexity",
    description: "This metric describes the conditions beyond the attacker’s control that must exist in order to exploit the vulnerability. Such conditions may require the collection of more information about the target, the presence of certain system configuration settings, or computational exceptions.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "L",
        name: "Low",
        description: "Specialized access conditions or extenuating circumstances do not exist. An attacker can expect repeatable success against the vulnerable component."
      },
      {
        id: "H",
        name: "High",
        description: "A successful attack depends on conditions beyond the attacker's control. That is, a successful attack cannot be accomplished at will, but requires the attacker to invest in some measurable amount of effort in preparation or execution against the vulnerable component before a successful attack can be expected. For example, a successful attack may require the attacker: to perform target-specific reconnaissance; to prepare the target environment to improve exploit reliability; or to inject herself into the logical network path between the target and the resource requested by the victim in order to read and/or modify network communications (e.g. a man in the middle attack)."
      }
    ]
  },
  MPR: {
    id: "MPR",
    name: "Modified Privileges Required",
    description: "This metric describes the level of privileges an attacker must possess before successfully exploiting the vulnerability. This Base Score increases as fewer privileges are required.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "N",
        name: "None",
        description: "The attacker is unauthorized prior to attack, and therefore does not require any access to settings or files to carry out an attack."
      },
      {
        id: "L",
        name: "Low",
        description: "The attacker is authorized with (i.e. requires) privileges that provide basic user capabilities that could normally affect only settings and files owned by a user. Alternatively, an attacker with Low privileges may have the ability to cause an impact only to non-sensitive resources."
      },
      {
        id: "H",
        name: "High",
        description: "The attacker is authorized with (i.e. requires) privileges that provide significant (e.g. administrative) control over the vulnerable component that could affect component-wide settings and files."
      }
    ]
  },
  MUI: {
    id: "MUI",
    name: "Modified User Interaction",
    description: "This metric captures the requirement for a user, other than the attacker, to participate in the successful compromise the vulnerable component. This metric determines whether the vulnerability can be exploited solely at the will of the attacker, or whether a separate user (or user-initiated process) must participate in some manner. The Base Score is highest when no user interaction is required.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "N",
        name: "None",
        description: "The vulnerable system can be exploited without any interaction from any user."
      },
      {
        id: "R",
        name: "Required",
        description: "Successful exploitation of this vulnerability requires a user to take some action before the vulnerability can be exploited."
      }
    ]
  },
  MS: {
    id: "MS",
    name: "Modified Scope",
    description: "Does a successful attack impact a component other than the vulnerable component? If so, the Base Score increases and the Confidentiality, Integrity and Authentication metrics should be scored relative to the impacted component.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "U",
        name: "Unchanged",
        description: "An exploited vulnerability can only affect resources managed by the same authority. In this case the vulnerable component and the impacted component are the same."
      },
      {
        id: "C",
        name: "Changed",
        description: "An exploited vulnerability can affect resources beyond the authorization privileges intended by the vulnerable component. In this case the vulnerable component and the impacted component are different."
      }
    ]
  },
  MC: {
    id: "MC",
    name: "Modified Confidentiality",
    description: "This metric measures the impact to the confidentiality of the information resources managed by a software component due to a successfully exploited vulnerability. Confidentiality refers to limiting information access and disclosure to only authorized users, as well as preventing access by, or disclosure to, unauthorized ones.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "N",
        name: "None",
        description: "There is no loss of confidentiality within the impacted component."
      },
      {
        id: "L",
        name: "Low",
        description: "There is some loss of confidentiality. Access to some restricted information is obtained, but the attacker does not have control over what information is obtained, or the amount or kind of loss is constrained. The information disclosure does not cause a direct, serious loss to the impacted component."
      },
      {
        id: "H",
        name: "High",
        description: "There is total loss of confidentiality, resulting in all resources within the impacted component being divulged to the attacker. Alternatively, access to only some restricted information is obtained, but the disclosed information presents a direct, serious impact."
      }
    ]
  },
  MI: {
    id: "MI",
    name: "Modified Integrity",
    description: "This metric measures the impact to integrity of a successfully exploited vulnerability. Integrity refers to the trustworthiness and veracity of information.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "N",
        name: "None",
        description: "There is no loss of integrity within the impacted component."
      },
      {
        id: "L",
        name: "Low",
        description: "Modification of data is possible, but the attacker does not have control over the consequence of a modification, or the amount of modification is constrained. The data modification does not have a direct, serious impact on the impacted component."
      },
      {
        id: "H",
        name: "High",
        description: "There is a total loss of integrity, or a complete loss of protection. For example, the attacker is able to modify any/all files protected by the impacted component. Alternatively, only some files can be modified, but malicious modification would present a direct, serious consequence to the impacted component."
      }
    ]
  },
  MA: {
    id: "MA",
    name: "Modified Availability",
    description: "This metric measures the impact to the availability of the impacted component resulting from a successfully exploited vulnerability. It refers to the loss of availability of the impacted component itself, such as a networked service (e.g., web, database, email). Since availability refers to the accessibility of information resources, attacks that consume network bandwidth, processor cycles, or disk space all impact the availability of an impacted component.",
    choices: [
      {
        id: "X",
        name: "Not Defined",
        description: "Use the value assigned to the corresponding Base Score metric."
      },
      {
        id: "N",
        name: "None",
        description: "There is no impact to availability within the impacted component."
      },
      {
        id: "L",
        name: "Low",
        description: "There is reduced performance or interruptions in resource availability. Even if repeated exploitation of the vulnerability is possible, the attacker does not have the ability to completely deny service to legitimate users. The resources in the impacted component are either partially available all of the time, or fully available only some of the time, but overall there is no direct, serious consequence to the impacted component."
      },
      {
        id: "H",
        name: "High",
        description: "There is total loss of availability, resulting in the attacker being able to fully deny access to resources in the impacted component; this loss is either sustained (while the attacker continues to deliver the attack) or persistent (the condition persists even after the attack has completed). Alternatively, the attacker has the ability to deny some availability, but the loss of availability presents a direct, serious consequence to the impacted component (e.g., the attacker cannot disrupt existing connections, but can prevent new connections; the attacker can repeatedly exploit a vulnerability that, in each instance of a successful attack, leaks a only small amount of memory, but after repeated exploitation causes a service to become completely unavailable)."
      }
    ]
  }
});

export const CVSS3_METRICS = Object.freeze(Object.fromEntries(Object.values(CVSS31_DEFINITION).map(m => [m.id, m.choices.map(c => c.id)])));
export const CVSS3_BASE_METRICS = Object.freeze(['AV', 'AC', 'PR', 'UI', 'S', 'C', 'I', 'A']);
export const CVSS3_TEMPORAL_METRICS = Object.freeze(['E', 'RL', 'RC']);
export const CVSS3_ENVIRONMENTAL_METRICS = Object.freeze(['CR', 'IR', 'AR', 'MAV', 'MAC', 'MPR', 'MUI', 'MS', 'MC', 'MI', 'MA']);

export function parseVector(vector) {
  // Vector to string
  const out = {};
  for (const part of (vector || '').slice(9).split('/')) {
    const kv = part.split(':');
    out[kv[0]] = kv.length > 1 ? kv[1] : null;
  }

  // Set undefined metrics
  for (const m of Object.keys(CVSS3_METRICS)) {
    if (!(m in out)) {
      out[m] = 'X';
    }
  }

  return out;
}

export function stringifyVector(parsedVector) {
  let out = 'CVSS:3.1';
  for (const [k, vs] of Object.entries(CVSS3_METRICS)) {
    if (k in parsedVector && vs.includes(parsedVector[k]) && parsedVector[k] !== 'X') {
      out += `/${k}:${parsedVector[k]}`;
    }
  }
  return out;
}

export function isValidVector(vector) {
  // Check CVSS identifier
  if (!vector || (!vector.startsWith('CVSS:3.0/') && !vector.startsWith('CVSS:3.1/'))) {
    return false;
  }

  const parsedVector = parseVector(vector) || {};

  // Only allowed values defined
  for (const [k, v] of Object.entries(parsedVector)) {
    if (!(k in CVSS3_METRICS) || !CVSS3_METRICS[k].includes(v)) {
      return false;
    }
  }

  // all base metrics defined
  for (const m of CVSS3_BASE_METRICS) {
    if (!(m in parsedVector)) {
      return false;
    }
  }

  return true;
}

function roundUp(num) {
  return Math.ceil(num * 10.0) / 10.0;
  // const intNum = Math.round(num * 100000);
  // if (intNum % 100000 === 0) {
  //   return intNum / 100000.0;
  // } else {
  //   return (Math.floor(intNum / 10000) + 1) / 10.0;
  // }
}

export function scoreFromVector(vector) {
  if (!isValidVector(vector)) {
    return null;
  }

  const parsedVector = parseVector(vector);

  // CVSS calculation based on https://www.first.org/cvss/v3.0/specification-document
  const scopeChanged = ([undefined, null, 'X'].includes(parsedVector.MS) ? parsedVector.S : parsedVector.MS) === 'C';
  // PR weight depends on S
  const prWeights = scopeChanged ? { X: 0.85, N: 0.85, L: 0.68, H: 0.50 } : { X: 0.85, N: 0.85, L: 0.62, H: 0.27 };
  const avWeights = { N: 0.85, A: 0.62, L: 0.55, P: 0.2 };
  const acWeights = { L: 0.77, H: 0.44 };
  const uiWeights = { N: 0.85, R: 0.62 };
  const ciaWeights = { N: 0, L: 0.22, H: 0.56 };
  const ciaRequirementsWeights = { X: 1, L: 0.5, M: 1, H: 1.5 };
  const weights = {
    // Base score
    AV: avWeights,
    AC: acWeights,
    PR: prWeights,
    UI: uiWeights,
    C: ciaWeights,
    I: ciaWeights,
    A: ciaWeights,

    // Temporal score
    E: { X: 1, U: 0.91, P: 0.94, F: 0.97, H: 1 },
    RL: { X: 1, U: 1, W: 0.97, T: 0.96, O: 0.95 },
    RC: { X: 1, U: 0.92, R: 0.96, C: 1 },

    // Environmental score
    CR: ciaRequirementsWeights,
    IR: ciaRequirementsWeights,
    AR: ciaRequirementsWeights,
    MAV: avWeights,
    MAC: acWeights,
    MPR: prWeights,
    MUI: uiWeights,
    MC: ciaWeights,
    MI: ciaWeights,
    MA: ciaWeights,
  };

  function metric(m, modifiedOnly = false) {
    let val = null;
    if (!modifiedOnly) {
      val = parsedVector['M' + m];
      if (val === 'X' || val === undefined) {
        val = null;
      }
    }

    if (val === null) {
      val = parsedVector[m];
    } else {
      m = 'M' + m;
    }

    if (modifiedOnly && [null, undefined].includes(val)) {
      val = 'X';
    }

    return weights[m][val];
  }

  // Environmental Score calculation (this is the final score shown to the customer)
  if (vector.startsWith('CVSS:3.0')) {
    let impact = Math.min(1 - ((1 - metric('C') * metric('CR', true)) *
      (1 - metric('I') * metric('IR', true)) *
      (1 - metric('A') * metric('AR', true))), 0.915);
    impact = scopeChanged ?
      7.52 * (impact - 0.029) - 3.25 * Math.pow(impact - 0.02, 15) :
      6.42 * impact;
    const exploitability = 8.22 * metric('AV') * metric('AC') * metric('PR') * metric('UI');
    let score = (impact <= 0) ? 0 :
      scopeChanged ? roundUp(Math.min(1.08 * (impact + exploitability), 10)) :
        roundUp(Math.min(impact + exploitability, 10));
    score = roundUp(score * metric('E', true) * metric('RL', true) * metric('RC', true));
    return score;
  } else {
    let impact = Math.min(1 - (
      (1 - metric('C') * metric('CR', true)) *
      (1 - metric('I') * metric('IR', true)) *
      (1 - metric('A') * metric('AR', true))
    ), 0.915);
    impact = scopeChanged ?
      7.52 * (impact - 0.029) - 3.25 * Math.pow(impact * 0.9731 - 0.02, 13) :
      6.42 * impact;
    const exploitability = 8.22 * metric('AV') * metric('AC') * metric('PR') * metric('UI');
    const score = (impact <= 0) ? 0 :
      scopeChanged ? 
        roundUp(roundUp(Math.min(1.08 * (impact + exploitability), 10)) * metric('E', true) * metric('RL', true) * metric('RC', true)) :
        roundUp(roundUp(Math.min(impact + exploitability, 10)) * metric('E', true) * metric('RL', true) * metric('RC', true));
    return score;
  }
}

export function levelNumberFromScore(score) {
  if (score === null || score === undefined) {
    return 1;
  }

  if (score >= 9.0) {
    return 5;
  } else if (score >= 7.0) {
    return 4;
  } else if (score >= 4.0) {
    return 3;
  } else if (score > 0.0) {
    return 2;
  } else {
    return 1;
  }
}

export function levelNameFromScore(score) {
  return ['Info', 'Low', 'Medium', 'High', 'Critical'][levelNumberFromScore(score) - 1];
}
