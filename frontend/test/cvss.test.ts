import { describe, test, expect } from 'vitest'
import { scoreFromVector } from '@/utils/cvss';

describe('CVSS score calculation', () => {
  for (const [vector, score] of Object.entries({
    'n/a': null,

    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H': 10.0,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N': 0.0,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N': 9.3,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:H/SI:H/SA:H': 7.9,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H/E:U': 9.1,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H/MVI:L/MSA:S': 9.8,
    'CVSS:4.0/AV:P/AC:H/AT:P/PR:H/UI:A/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N': 1.0,
    'CVSS:4.0/AV:L/AC:L/AT:N/PR:L/UI:P/VC:N/VI:H/VA:H/SC:N/SI:L/SA:L': 5.2,
    'CVSS:4.0/AV:L/AC:L/AT:N/PR:L/UI:P/VC:N/VI:H/VA:H/SC:N/SI:L/SA:L/E:P/CR:H/IR:M/AR:H/MAV:A/MAT:P/MPR:N/MVI:H/MVA:N/MSI:H/MSA:N/S:N/V:C/U:Amber': 4.7,
    'CVSS:4.0/AV:N/AC:H/AT:N/PR:H/UI:N/VC:N/VI:N/VA:H/SC:H/SI:H/SA:H/CR:L/IR:L/AR:L': 5.8,
    'CVSS:4.0/AV:F/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N': null,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/ui:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N': null,
    'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/SC:N/SI:N/SA:N': null,

    'CVSS:3.1/AV:N': null,
    'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/XX:X': null,
    'CVSS:3.1/AV:J/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L': null,
    'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N': 0.0,
    'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L': 4.6,
    'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L': 5.5,
    'CVSS:3.1/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L': 7.0,
    'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H': 10.0,
    'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N/CR:H': 10.0,
    'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H': 9.9,
    'CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:H': 9.0,
    'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:T/RC:U': 8.4,
    'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:X/RC:U/CR:M/IR:H/AR:X/MAV:A/MAC:L/MPR:L/MUI:R/MS:U/MC:L/MI:L/MA:X': 5.7,

    'CVSS:3.0/AV:N': null,
    'CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/XX:X': null,
    'CVSS:3.0/AV:J/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L': null,
    'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N': 0.0,
    'CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L': 4.6,
    'CVSS:3.0/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L': 5.5,
    'CVSS:3.0/AV:A/AC:H/PR:N/UI:R/S:C/C:H/I:L/A:L': 7.0,
    'CVSS:3.0/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H': 9.9,
    'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H': 10.0,
    'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:T/RC:U': 8.4,
    'CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:P/RL:X/RC:U/CR:M/IR:H/AR:X/MAV:A/MAC:L/MPR:L/MUI:R/MS:U/MC:L/MI:L/MA:X': 5.7,
  })) {
    test(vector, () => expect(scoreFromVector(vector)).toBe(score));
  }
});
