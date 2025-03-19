import { groupBy, orderBy } from "lodash-es";
import { scoreFromVector, levelNumberFromLevelName, levelNumberFromScore, levelNameFromScore } from "./cvss";

export type SortFindingsOptions<T extends PentestFinding> = {
  findings: T[];
  projectType: ProjectType;
  overrideFindingOrder?: boolean;
  topLevelFields?: boolean;
}

export type FindingGroup<T extends PentestFinding = PentestFinding> = {
  label: string;
  findings: T[];
}


function getSortKeyPart(options: { finding: PentestFinding, ordering: FindingOrderingDefinition, projectType: ProjectType; topLevelFields?: boolean, cvssByLevel?: boolean}) {
  const v = options.topLevelFields ? (options.finding as any)[options.ordering.field] : options.finding.data[options.ordering.field];
  const d = options.projectType.finding_fields.find(f => f.id === options.ordering.field);
  if (!d || d.type in [FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER] || Array.isArray(v) || typeof v === 'object') {
    // Sorting by field is not supported
    return '';
  } else if (d.type === FieldDataType.CVSS) {
    const score = scoreFromVector(v) || 0;
    if (options.cvssByLevel) {
      return levelNumberFromScore(score);
    } else {
      return score;
    }
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
}

function getGroupLabel(options: { finding: PentestFinding, projectType: ProjectType; topLevelFields?: boolean }) {
  if ((options.projectType.finding_grouping || []).length === 0) {
    return '';
  }

  const groupingField = options.projectType.finding_grouping![0]!.field;
  const v = (options.topLevelFields ? options.finding as any : options.finding.data)[groupingField];
  const d = options.projectType.finding_fields.find(f => f.id === groupingField)!;

  if (v === null || v === undefined) {
    return '';
  } else if (d.type === FieldDataType.ENUM) {
    return d.choices?.find(c => c.value === v)?.label || '';
  } else if (d.type === FieldDataType.CVSS) {
    return levelNameFromScore(scoreFromVector(v) || 0.0).toLowerCase();
  } else {
    return `${v}`;
  }
}


export function sortFindings<T extends PentestFinding>(options: SortFindingsOptions<T>): T[] {
  if (options.overrideFindingOrder || options.projectType.finding_ordering.length === 0) {
    return orderBy(options.findings, ['order', 'created']);
  } else {
    return orderBy(
      options.findings,
      options.projectType.finding_ordering.map(o => (f: T) => getSortKeyPart({ ...options, finding: f, ordering: o })).concat(f => f.created),
      options.projectType.finding_ordering.map(o => o.order || SortOrder.ASC).concat([SortOrder.ASC])
    );
  }
}


export function groupFindings<T extends PentestFinding>(options: SortFindingsOptions<T>): FindingGroup<T>[] {
  if ((options.projectType.finding_grouping || []).length === 0) {
    return [{ label: '', findings: sortFindings(options) }];
  }

  // Group
  const findingsAnnotated = options.findings.map(finding => ({
    finding,
    groupKey: getSortKeyPart({
      ...options,
      finding,
      ordering: options.projectType.finding_grouping![0]!,
      cvssByLevel: true,
    }),
  }))
  const groups = groupBy(findingsAnnotated, fa => fa.groupKey);

  // Sort groups
  let groupsSorted: typeof findingsAnnotated[];
  if (options.overrideFindingOrder || options.projectType.finding_ordering.length === 0) {
    groupsSorted = orderBy(Object.values(groups), [g => Math.min(...g.map(f => f.finding.order))], SortOrder.ASC);
  } else {
    groupsSorted = orderBy(
      Object.values(groups),
      [g => g[0]!.groupKey], 
      [options.projectType.finding_grouping![0]!.order || SortOrder.ASC]
    );
  }
  
  // Format groups
  return groupsSorted.map(g => ({
    label: getGroupLabel({ ...options, finding: g[0]!.finding }),
    findings: sortFindings({
      ...options,
      findings: g.map(fa => fa.finding)
    }),
  }));
}


export function getFindingRiskLevel(options: { finding: PentestFinding, projectType: ProjectType, topLevelFields?: boolean }) {
  const findingData = options.topLevelFields ? options.finding as PentestFinding['data'] : options.finding.data;

  if (options.projectType.finding_fields.some(f => f.id === 'severity')) {
    return levelNumberFromLevelName(findingData.severity);
  } else if (options.projectType.finding_fields.some(f => f.id === 'cvss')) {
    return levelNumberFromScore(scoreFromVector(findingData.cvss));
  } else {
    return 'unknown';
  }
}
