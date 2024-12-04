import { orderBy } from "lodash-es";
import { scoreFromVector, levelNumberFromLevelName, levelNumberFromScore } from "./cvss";

export function sortFindings<T extends PentestFinding>({ findings, projectType, overrideFindingOrder = false, topLevelFields = false }: {findings: T[], projectType: ProjectType, overrideFindingOrder?: boolean, topLevelFields?: boolean}): T[] {
  if (overrideFindingOrder || projectType.finding_ordering.length === 0) {
    return orderBy(findings, ['order', 'created']);
  } else {
    return orderBy(
      findings,
      projectType.finding_ordering.map(o => (finding: T) => {
        const v = topLevelFields ? (finding as any)[o.field] : finding.data[o.field];
        const d = projectType.finding_fields.find(f => f.id === o.field);
        if (!d || d.type in [FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER] || Array.isArray(v) || typeof v === 'object') {
          // Sorting by field is not supported
          return '';
        } else if (d.type === FieldDataType.CVSS) {
          return scoreFromVector(v) || 0;
        } else if (d.type === FieldDataType.CWE) {
          if (!v) {
            return -1;
          } 
          return Number(v.replace('CWE-'))
        } else if (d.type === FieldDataType.ENUM) {
          return d.choices!.findIndex(c => c.value === v);
        } else if (v !== null && v !== undefined) {
          return v;
        } else if (d.type === FieldDataType.NUMBER) {
          return 0;
        } else if (d.type === FieldDataType.BOOLEAN) {
          return false;
        } else {
          return '';
        }
      }).concat(f => f.created),
      projectType.finding_ordering.map(o => o.order).concat([SortOrder.ASC])
    );
  }
}


export function getFindingRiskLevel(options: { finding: PentestFinding, projectType: ProjectType }) {
  if (options.projectType.finding_fields.some(f => f.id === 'severity')) {
    return levelNumberFromLevelName(options.finding.data.severity);
  } else if (options.projectType.finding_fields.some(f => f.id === 'cvss')) {
    return levelNumberFromScore(scoreFromVector(options.finding.data.cvss));
  } else {
    return 'unknown';
  }
}
