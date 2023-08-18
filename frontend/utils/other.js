import { orderBy } from "lodash";
import { scoreFromVector } from "./cvss";

export const EditMode = Object.freeze({
  READONLY: 'READONLY',
  EDIT: 'EDIT',
});

export const mfaMethodChoices = Object.freeze([
  { value: 'fido2', text: 'Security Key (FIDO2)', icon: 'mdi-key' },
  { value: 'totp', text: 'Authenticator App (TOTP)', icon: 'mdi-cellphone-key' },
  { value: 'backup', text: 'Backup Codes', icon: 'mdi-lock-reset' },
]);

export function sortFindings({ findings, projectType, overrideFindingOrder = false, topLevelFields = false }) {
  if (overrideFindingOrder) {
    return orderBy(findings, ['order', 'created']);
  } else {
    return orderBy(
      findings, 
      projectType.finding_ordering.map(o => (finding) => {
        const v = topLevelFields ? finding[o.field] : finding.data[o.field];
        const d = projectType.finding_fields[o.field];
        if (!d || d.type in ['list', 'object', 'user'] || Array.isArray(v) || typeof v === 'object') {
          // Sorting by field is unsupported
          return '';
        } else if (d.type === 'cvss') {
          return scoreFromVector(v) || 0;
        } else if (d.type === 'enum') {
          return d.choices.findIndex(c => c.value === v);
        } else if (d !== null && d !== undefined) {
          return v;
        } else if (d.type === 'number') {
          return 0;
        } else if (d.type === 'boolean') {
          return false;
        } else {
          return '';
        }
      }).concat(f => f.created),
      projectType.finding_ordering.map(o => o.order).concat(['asc'])
    );
  }
}
