import { scoreFromVector } from '@/utils/cvss';

describe('CVSS score calculation', () => {
  for (const [vector, score] of Object.entries({
    'n/a': null,

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
  })) {
    test(vector, () => expect(scoreFromVector(vector)).toBe(score));
  }
});
