import { describe, it, expect } from 'vitest';
import {
  commentLocationUrl,
  groupCommentsByLocation,
  parseCommentLocation,
  sortComments,
} from '~/utils/comments';
import type { Comment, PentestFinding, ProjectType, ReportSection } from '#imports';

function createProjectType(): ProjectType {
  return {
    finding_fields: [
      { id: 'title', type: 'string', label: 'Title', default: '' },
      { id: 'description', type: 'markdown', label: 'Description', default: '' },
      { id: 'affected_components', type: 'list', label: 'Affected', items: { type: 'string', default: '' }, default: [] },
      { id: 'details', type: 'object', label: 'Details', properties: [
        { id: 'impact', type: 'markdown', label: 'Impact', default: '' },
        { id: 'likelihood', type: 'markdown', label: 'Likelihood', default: '' },
      ], default: {} },
    ],
    report_sections: [
      { id: 'executive_summary', label: 'Executive Summary', fields: [
        { id: 'summary', type: 'markdown', label: 'Summary', default: '' },
        { id: 'conclusion', type: 'markdown', label: 'Conclusion', default: '' },
      ] },
      { id: 'scope', label: 'Scope', fields: [
        { id: 'scope_text', type: 'markdown', label: 'Scope', default: '' },
      ] },
    ],
  } as ProjectType;
}

function createComment(id: string, path: string, overrides: Partial<Comment> = {}): Comment {
  return {
    id,
    path,
    text: '',
    status: 'open' as Comment['status'],
    user: null,
    text_range: null,
    text_original: null,
    answers: [],
    created: `2024-01-0${id}T00:00:00Z`,
    ...overrides,
  } as Comment;
}

describe('parseCommentLocation', () => {
  it('parses finding and section paths', () => {
    expect(parseCommentLocation('findings.f1.data.title')).toEqual({ type: 'findings', id: 'f1', dataPath: 'title' });
    expect(parseCommentLocation('sections.s1.data.summary')).toEqual({ type: 'sections', id: 's1', dataPath: 'summary' });
    expect(parseCommentLocation('findings.f1.data.affected_components.[2]')).toEqual({
      type: 'findings',
      id: 'f1',
      dataPath: 'affected_components.[2]',
    });
  });

  it('returns null for paths outside findings/sections', () => {
    expect(parseCommentLocation('notes.n1.data.text')).toBeNull();
    expect(parseCommentLocation('invalid')).toBeNull();
  });
});

describe('commentLocationUrl', () => {
  it('builds section and finding URLs and rejects invalid paths', () => {
    expect(commentLocationUrl('p1', 'sections.s1.data.summary')).toBe('/projects/p1/reporting/sections/s1/');
    expect(commentLocationUrl('p1', 'findings.f1.data.title')).toBe('/projects/p1/reporting/findings/f1/');
    expect(commentLocationUrl('p1', 'invalid')).toBeNull();
  });
});

describe('sortComments', () => {
  const projectType = createProjectType();
  const sections = [
    { id: 'executive_summary', label: 'Executive Summary' },
    { id: 'scope', label: 'Scope' },
  ] as ReportSection[];
  const findings = [
    { id: 'f2', data: { title: 'Finding 2' } },
    { id: 'f1', data: { title: 'Finding 1' } },
  ] as PentestFinding[];

  it('sorts sections before findings, both in project sidebar order', () => {
    const comments = [
      createComment('1', 'findings.f1.data.title'),
      createComment('2', 'sections.scope.data.scope_text'),
      createComment('3', 'sections.executive_summary.data.summary'),
      createComment('4', 'findings.f2.data.title'),
    ];
    const sorted = sortComments(comments, { projectType, sections, findings });
    expect(sorted.map(c => c.id)).toEqual(['3', '2', '4', '1']);
  });

  it('orders fields by their definition index within a location', () => {
    const comments = [
      createComment('1', 'findings.f1.data.description'),
      createComment('2', 'findings.f1.data.title'),
    ];
    const sorted = sortComments(comments, { projectType, basePath: 'findings.f1.data.' });
    expect(sorted.map(c => c.id)).toEqual(['2', '1']);
  });

  it('orders comments on the same field by text_range.from, with null text_range last', () => {
    const comments = [
      createComment('1', 'findings.f1.data.title', { text_range: { from: 10, to: 15 } }),
      createComment('2', 'findings.f1.data.title', { text_range: { from: 2, to: 5 } }),
      createComment('3', 'findings.f1.data.title', { text_range: null }),
    ];
    const sorted = sortComments(comments, { projectType, basePath: 'findings.f1.data.' });
    expect(sorted.map(c => c.id)).toEqual(['2', '1', '3']);
  });

  it('orders nested list items by index, then text_range within the same item', () => {
    const comments = [
      createComment('1', 'findings.f1.data.affected_components.[1]'),
      createComment('2', 'findings.f1.data.affected_components.[0]', { text_range: { from: 5, to: 10 } }),
      createComment('3', 'findings.f1.data.affected_components.[0]', { text_range: { from: 1, to: 2 } }),
      createComment('4', 'findings.f1.data.affected_components.[3]'),
    ];
    const sorted = sortComments(comments, { projectType, basePath: 'findings.f1.data.' });
    expect(sorted.map(c => c.id)).toEqual(['3', '2', '1', '4']);
  });

  it('filters out comments outside the requested basePath', () => {
    const comments = [
      createComment('1', 'findings.f1.data.title'),
      createComment('2', 'findings.f2.data.title'),
      createComment('3', 'sections.executive_summary.data.summary'),
    ];
    const sorted = sortComments(comments, { projectType, basePath: 'findings.f1.data.' });
    expect(sorted.map(c => c.id)).toEqual(['1']);
  });
});

describe('groupCommentsByLocation', () => {
  const projectType = createProjectType();
  const sections = [{ id: 'executive_summary', label: 'Executive Summary' }] as ReportSection[];
  const findings = [{ id: 'f1', data: { title: 'SQL Injection' } }] as PentestFinding[];

  it('groups by location then by field, preserving the input sort order', () => {
    const sorted = sortComments([
      createComment('1', 'sections.executive_summary.data.summary'),
      createComment('2', 'sections.executive_summary.data.conclusion'),
      createComment('3', 'findings.f1.data.title'),
    ], { projectType, sections, findings });

    const groups = groupCommentsByLocation(sorted, { projectId: 'p1', sections, findings });

    expect(groups).toHaveLength(2);
    expect(groups[0]!.title).toBe('Executive Summary');
    expect(groups[0]!.url).toBe('/projects/p1/reporting/sections/executive_summary/');
    expect(groups[0]!.fieldGroups.map(g => g.path)).toEqual([
      'sections.executive_summary.data.summary',
      'sections.executive_summary.data.conclusion',
    ]);
    expect(groups[1]!.title).toBe('SQL Injection');
    expect(groups[1]!.url).toBe('/projects/p1/reporting/findings/f1/');
  });

  it('falls back to the location id when section/finding metadata is missing', () => {
    const groups = groupCommentsByLocation([
      createComment('1', 'findings.missing.data.title'),
    ], { projectId: 'p1', sections: [], findings: [] });
    expect(groups).toHaveLength(1);
    expect(groups[0]!.title).toBe('missing');
  });

  it('drops comments whose path is not a finding or section field', () => {
    const groups = groupCommentsByLocation([
      createComment('1', 'notes.n1.data.text'),
    ], { projectId: 'p1', sections: [], findings: [] });
    expect(groups).toHaveLength(0);
  });
});
