import { groupBy, orderBy } from 'lodash-es';
import type { Comment, FieldDefinition, PentestFinding, ProjectType, ReportSection } from '#imports';

export type CommentLocation = { type: string, id: string, dataPath: string };
export type CommentFieldGroup = { path: string, comments: Comment[] };
export type CommentLocationGroup = {
  locationKey: string;
  title: string;
  url: string;
  fieldGroups: CommentFieldGroup[];
};

export function parseCommentLocation(path: string): CommentLocation | null {
  const parts = path.split('.');
  if (parts.length < 3 || !['findings', 'sections'].includes(parts[0]!) || parts[2] !== 'data') {
    return null;
  }
  return { type: parts[0]!, id: parts[1]!, dataPath: parts.slice(3).join('.') };
}

function locationKey(path: string): string | null {
  const loc = parseCommentLocation(path);
  return loc ? `${loc.type}.${loc.id}` : null;
}

export function commentLocationUrl(projectId: string, path: string): string | null {
  const loc = parseCommentLocation(path);
  if (!loc) {
    return null;
  }
  return `/projects/${projectId}/reporting/${loc.type}/${loc.id}/`;
}

function normalizeRoutePath(path: string): string {
  return path.replace(/\/+$/, '') || '/';
}

export function isOnCommentLocationRoute(currentPath: string, locationUrl: string): boolean {
  const base = normalizeRoutePath(locationUrl);
  const path = normalizeRoutePath(currentPath);
  return path === base || path.startsWith(base + '/');
}

export function commentFieldDefinitions(projectType: ProjectType, location: CommentLocation): FieldDefinition[] {
  return location.type === 'findings' ? projectType.finding_fields :
    location.type === 'sections' ? projectType.report_sections.find(s => s.id === location.id)?.fields || [] :
    [];
}

function fieldOrderIndex(path: string, projectType: ProjectType): number {
  const loc = parseCommentLocation(path);
  if (!loc || !loc.dataPath) {
    return Number.MAX_SAFE_INTEGER;
  }
  const fieldId = loc.dataPath.split('.')[0]!;
  const idx = commentFieldDefinitions(projectType, loc).findIndex(f => f.id === fieldId);
  return idx === -1 ? Number.MAX_SAFE_INTEGER : idx;
}

export function sortComments(
  comments: Comment[],
  options: {
    projectType: ProjectType,
    basePath?: string,
    sections?: ReportSection[],
    findings?: PentestFinding[],
  },
): Comment[] {
  const { projectType, basePath, sections, findings } = options;
  const filtered = basePath
    ? comments.filter(c => c.path.startsWith(basePath))
    : comments.filter(c => locationKey(c.path) !== null);

  // Project-wide order mirrors the project sidebar: sections first (in projectType order), then findings.
  let locationOrder: Map<string, number> | null = null;
  if (sections && findings) {
    locationOrder = new Map();
    sections.forEach((s, i) => locationOrder!.set(`sections.${s.id}`, i));
    findings.forEach((f, i) => locationOrder!.set(`findings.${f.id}`, sections.length + i));
  }

  return orderBy(filtered, [
    c => locationOrder ? (locationOrder.get(locationKey(c.path)!) ?? Number.MAX_SAFE_INTEGER) : 0,
    c => fieldOrderIndex(c.path, projectType),
    // Keeps nested list/object sub-paths in stable order (e.g. affected_components.[0] before [1]).
    'path',
    c => c.text_range?.from ?? Number.MAX_SAFE_INTEGER,
    'created',
  ]);
}

export function groupCommentsByLocation(
  comments: Comment[],
  options: { projectId: string, sections: ReportSection[], findings: PentestFinding[] },
): CommentLocationGroup[] {
  const titleFor = (loc: CommentLocation) => loc.type === 'sections'
    ? (options.sections.find(s => s.id === loc.id)?.label || loc.id)
    : (options.findings.find(f => f.id === loc.id)?.data.title || loc.id);

  // Comments arrive pre-sorted; groupBy preserves insertion order for string keys, so group order
  // matches the sort order without manual bookkeeping.
  const valid = comments.filter(c => locationKey(c.path) !== null);
  return Object.entries(groupBy(valid, c => locationKey(c.path)!)).map(([key, locComments]) => {
    const loc = parseCommentLocation(locComments[0]!.path)!;
    return {
      locationKey: key,
      title: titleFor(loc),
      url: commentLocationUrl(options.projectId, locComments[0]!.path)!,
      fieldGroups: Object.entries(groupBy(locComments, 'path'))
        .map(([path, comments]) => ({ path, comments })),
    };
  });
}
