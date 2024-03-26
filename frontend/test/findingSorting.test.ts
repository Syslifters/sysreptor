import { describe, it, expect } from 'vitest'
import { addDays } from "date-fns";
import reverse from 'lodash/reverse';
import { sortFindings } from '@/stores/project';
import { SortOrder } from "~/utils/types";
import type { FindingOrderingDefinition, PentestFinding, ProjectType } from "~/utils/types";

function testFindingSort({ findings, findingOrdering = [], overrideFindingOrder = false }: { findings: PentestFinding[], findingOrdering?: FindingOrderingDefinition[], overrideFindingOrder?: boolean}) {
  const unorderedFindings = findings.map((f, idx) => ({ ...f, data: { ...(f.data || {}), title: 'f' + (idx + 1) } })) as PentestFinding[];
  const projectType = {
    finding_fields: {
      cvss: { type: 'cvss', label: 'CVSS', default: 'n/a' },
      field_string: { type: 'string', label: 'String Field', default: 'test' },
      field_markdown: { type: 'markdown', label: 'Markdown Field', default: '# test\nmarkdown' },
      field_cvss: { type: 'cvss', label: 'CVSS Field', default: 'n/a' },
      field_date: { type: 'date', label: 'Date Field', default: '2022-01-01' },
      field_int: { type: 'number', label: 'Number Field', default: 10 },
      field_bool: { type: 'boolean', label: 'Boolean Field', default: false },
      field_enum: { type: 'enum', label: 'Enum Field', choices: [{ value: 'enum1', label: 'Enum Value 1' }, { value: 'enum2', label: 'Enum Value 2' }], default: 'enum2' },
    },
    finding_ordering: findingOrdering,
  } as unknown as ProjectType;
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
      ] as unknown as PentestFinding[],
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
        })) as unknown as PentestFinding[],
        findingOrdering: config.order,
      });
    });
  }
});
