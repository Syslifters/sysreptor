import { sortBy } from "lodash";
import { scoreFromVector } from "./cvss";

export function sortFindings(findings) {
  return sortBy(findings, [f => -scoreFromVector(f.data ? f.data.cvss : f.cvss), f => f.created, f => f.id]);
}

export const EditMode = Object.freeze({
  READONLY: 'READONLY',
  EDIT: 'EDIT',
});

export const mfaMethodChoices = Object.freeze([
  { value: 'fido2', text: 'Security Key (FIDO2)', icon: 'mdi-key' },
  { value: 'totp', text: 'Authenticator App (TOTP)', icon: 'mdi-cellphone-key' },
  { value: 'backup', text: 'Backup Codes', icon: 'mdi-lock-reset' },
]);
