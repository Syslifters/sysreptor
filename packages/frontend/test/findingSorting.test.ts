import { describe, it, expect } from 'vitest'
import { addDays } from "date-fns";
import { pick, reverse } from 'lodash-es';
import { sortFindings } from '@base/utils/project';
import { type FindingOrderingDefinition, type PentestFinding, type ProjectType, SortOrder } from "#imports";

function createProjectType(obj: Partial<ProjectType>) {
  return {
    finding_fields: [
      { id: 'cvss', type: 'cvss', label: 'CVSS', default: 'n/a' },
      { id: 'field_string', type: 'string', label: 'String Field', default: 'test' },
      { id: 'field_markdown', type: 'markdown', label: 'Markdown Field', default: '# test\nmarkdown' },
      { id: 'field_cvss', type: 'cvss', label: 'CVSS Field', default: 'n/a' },
      { id: 'field_date', type: 'date', label: 'Date Field', default: '2022-01-01' },
      { id: 'field_int', type: 'number', label: 'Number Field', default: 10 },
      { id: 'field_bool', type: 'boolean', label: 'Boolean Field', default: false },
      { id: 'field_enum', type: 'enum', label: 'Enum Field', choices: [{ value: 'enum1', label: 'Enum Value 1' }, { value: 'enum2', label: 'Enum Value 2' }], default: 'enum2' },
      {id: 'field_combobox', type: 'combobox', label: 'Combobox Field', suggestions: ['value 1', 'value 2'], default: 'value1'},
    ],
    finding_ordering: [],
    finding_grouping: null,
    ...obj
  } as Partial<ProjectType> as ProjectType;
}


function testFindingSort({ findings, findingOrdering = [], overrideFindingOrder = false }: { findings: PentestFinding[], findingOrdering?: FindingOrderingDefinition[], overrideFindingOrder?: boolean}) {
  const unorderedFindings = findings.map((f, idx) => ({ ...f, data: { ...(f.data || {}), title: 'f' + (idx + 1) } })) as PentestFinding[];
  const projectType = createProjectType({
    finding_ordering: findingOrdering,
  });
  const sortedFindings = sortFindings({
    findings: reverse(unorderedFindings),
    projectType,
    overrideFindingOrder,
  });

  const sortedFindingTitles = sortedFindings.map(f => f.data.title);
  const expectedFindingTitles = [];
  for (let i = 0; i < sortedFindingTitles.length; i++) {
    expectedFindingTitles.push('f' + (i + 1));
  }
  expect(sortedFindingTitles).toEqual(expectedFindingTitles);
}

describe('Finding Sorting', () => {
  it('should sort findings by order', () => {
    testFindingSort({
      findings: [
        { order: 1 },
        { order: 2 },
        { order: 3 },
      ] as unknown as PentestFinding[],
      overrideFindingOrder: true,
    });
  });

  it('should use created date as fallback sort', () => {
    testFindingSort({
      findings: [
        { order: 0, created: addDays(new Date(), -2).toISOString() },
        { order: 0, created: addDays(new Date(), -1).toISOString() },
        { order: 0, created: addDays(new Date(), -0).toISOString() },
      ] as Partial<PentestFinding>[] as PentestFinding[],
      overrideFindingOrder: true,
    });
  });

  for (const config of [
    { order: [{ field: 'cvss', order: SortOrder.DESC }], findings: [{ cvss: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H' }, { cvss: 'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L' }, { cvss: null }] }, // CVSS
    { order: [{ field: 'field_string', order: SortOrder.ASC }], findings: [{ field_string: 'aaa' }, { field_string: 'bbb' }, { field_string: 'ccc' }] }, // string field
    { order: [{ field: 'field_int', order: SortOrder.ASC }], findings: [{ field_int: 1 }, { field_int: 10 }, { field_int: 13 }] }, // number
    { order: [{ field: 'field_enum', order: SortOrder.ASC }], findings: [{ field_enum: 'enum1' }, { field_enum: 'enum2' }] }, // enum
    { order: [{ field: 'field_date', order: SortOrder.ASC }], findings: [{ field_date: null }, { field_date: '2023-01-01' }, { field_date: '2023-06-01' }] }, // date
    { order: [{ field: 'field_string', order: SortOrder.ASC }, { field: 'field_markdown', order: SortOrder.ASC }], findings: [{ field_string: 'aaa', field_markdown: 'xxx' }, { field_string: 'aaa', field_markdown: 'yyy' }, { field_string: 'bbb', field_markdown: 'zzz' }] }, // multiple fields: string, markdown
    { order: [{ field: 'field_bool', order: SortOrder.DESC }, { field: 'cvss', order: SortOrder.DESC }], findings: [{ field_bool: true, cvss: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H' }, { field_bool: true, cvss: 'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:L' }, { field_bool: false, cvss: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H' }] }, // multiple fields: -bool, -cvss
    { order: [{ field: 'field_enum', order: SortOrder.ASC }, { field: 'field_int', order: SortOrder.DESC }], findings: [{ field_enum: 'enum1', field_int: 2 }, { field_enum: 'enum1', field_int: 1 }, { field_enum: 'enum2', field_int: 10 }, { field_enum: 'enum2', field_int: 9 }] }, // multiple fields with mixed asc/desc: enum, -number
  ]) {
    it(`should sort findings by ${JSON.stringify(config.order)}`, () => {
      testFindingSort({
        findings: config.findings.map(f => ({
          created: new Date().toISOString(),
          order: 0,
          data: f,
        } as Partial<PentestFinding> as PentestFinding)),
        findingOrdering: config.order,
      });
    });
  }
});


function testFindingGrouping(options: { 
  findingGrouping: FindingOrderingDefinition[]|null, 
  findings: Record<string, any>[], 
  expectedGroups: {label: string, findings: string[]}[],
  findingOrdering?: FindingOrderingDefinition[], 
}) {
  const findings = options.findings.map(data => ({
    id: uuidv4(),
    created: new Date().toISOString(),
    order: 0,
    data,
  } as Partial<PentestFinding> as PentestFinding));
  const projectType = createProjectType({
    finding_grouping: options.findingGrouping,
    finding_ordering: options.findingOrdering || [],
  });
  const groups = groupFindings({ findings, projectType });
  const groupTitles = groups.map(g => ({label: g.label, findings: g.findings.map(f => f.data.title)}));
  expect(groupTitles).toEqual(options.expectedGroups);
}

describe('Finding Grouping', () => {
  for (const config of [
    // Not grouped: everything in a single group
    {findingGrouping: null, findings: [{title: 'f1'}, {title: 'f2'}, {title: 'f3'}], expectedGroups: [{label: '', findings: ['f1', 'f2', 'f3']}]},
    {findingGrouping: [], findings: [{title: 'f1'}, {title: 'f2'}, {title: 'f3'}], expectedGroups: [{label: '', findings: ['f1', 'f2', 'f3']}]},
    // Group by single field
    {findingGrouping: [{field: 'field_enum', order: SortOrder.ASC}], findings: [{title: 'f1', field_enum: 'enum2'}, {title: 'f2', field_enum: 'enum1'}, {title: 'f3', field_enum: 'enum2'}], expectedGroups: [{label: 'Enum Value 1', findings: ['f2']}, {label: 'Enum Value 2', findings: ['f1', 'f3']}]},
    {findingGrouping: [{field: 'field_combobox', order: SortOrder.ASC}], findings: [{title: 'f1', field_combobox:  'g1'}, {title: 'f2', field_combobox:  'g2'}, {title: 'f3', field_combobox:  'g1'}], expectedGroups: [{label: 'g1', findings: ['f1', 'f3']}, {label: 'g2', findings: ['f2']}]},
    {findingGrouping: [{field: 'field_string', order: SortOrder.ASC}], findings: [{title: 'f1', field_string: 'g1'}, {title: 'f2', field_string: 'g2'}, {title: 'f3', field_string: 'g1'}], expectedGroups: [{label: 'g1', findings: ['f1', 'f3']}, {label: 'g2', findings: ['f2']}]},
    {findingGrouping: [{field: 'field_bool', order: SortOrder.ASC}], findings: [{title: 'f1', field_bool: false}, {title: 'f2', field_bool: true}, {title: 'f3', field_bool: false}], expectedGroups: [{label: 'false', findings: ['f1', 'f3']}, {label: 'true', findings: ['f2']}]},
    {findingGrouping: [{field: 'field_date', order: SortOrder.ASC}], findings: [{title: 'f1', field_date: '2023-01-01'}, {title: 'f2', field_date: '2023-06-01'}, {title: 'f3', field_date: '2023-01-01'}], expectedGroups: [{label: '2023-01-01', findings: ['f1', 'f3']}, {label: '2023-06-01', findings: ['f2']}]},
    {findingGrouping: [{field: 'field_cvss', order: SortOrder.DESC}], findings: [{title: 'f1', field_cvss: 'n/a'}, {title: 'f2', field_cvss: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H'}, {title: 'f3', field_cvss: 'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:N/I:N/A:N'}], expectedGroups: [{label: 'critical', findings: ['f2']}, {label: 'info', findings: ['f1', 'f3']}]},
  ]) {
    it(`should group findings ${JSON.stringify(config.findingGrouping)}`, () => {
      testFindingGrouping(config);
    })
  }

  for (const config of [
    {groupOrder: SortOrder.ASC, findingOrder: SortOrder.DESC, expectedGroups: [{'label': 'g1', 'findings': ['g1f2', 'g1f1']}, {'label': 'g2', 'findings': ['g2f2', 'g2f1']}]},
    {groupOrder: SortOrder.DESC, findingOrder: SortOrder.ASC, expectedGroups: [{'label': 'g2', 'findings': ['g2f1', 'g2f2']}, {'label': 'g1', 'findings': ['g1f1', 'g1f2']}]},
  ]) {
    it(`should sort groups ${JSON.stringify(pick(config, ['groupOrder', 'findingOrder']))}`, () => {
      testFindingGrouping({
        findingGrouping: [{field: 'field_string', order: config.groupOrder}],
        findingOrdering: [{field: 'field_int', order: config.findingOrder}],
        findings: [
          {title: 'g1f2', field_string: 'g1', field_int: 3},
          {title: 'g2f1', field_string: 'g2', field_int: 2},
          {title: 'g1f1', field_string: 'g1', field_int: 1},
          {title: 'g2f2', field_string: 'g2', field_int: 4},
        ],
        expectedGroups: config.expectedGroups,
      })
    })
  }
});
