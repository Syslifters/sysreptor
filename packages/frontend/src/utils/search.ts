import { get, groupBy, sortBy } from "lodash-es";
import { SearchCursor, Text } from "@sysreptor/markdown/editor";

export type SearchResultMatch = {
  field: string;
  from: number;
  to: number;
  matchingText: string;
  previewText: string;
  previewFrom: number;
  previewTo: number;
};

export type SearchResult<T> = {
  item: T;
  matches: SearchResultMatch[];
};
export type NoteSearchResults<T extends NoteBase> = (SearchResult<T> & { children: NoteSearchResults<T> })[];


function searchField(obj: any, search: string, field?: string): SearchResultMatch[] {
  const fieldValue = field ? get(obj, field) : obj;
  if (typeof fieldValue !== 'string') {
    return [];
  }

  const text = Text.of(fieldValue.split(/\r?\n/));
  return Array.from(new SearchCursor(text, search, undefined, undefined, x => x.toLowerCase()))
    .map((m) => {
      const matchingText = text.sliceString(m.from, m.to);
      const matchingLine = text.lineAt(m.from); 
      const lineFrom = m.from - matchingLine.from;
      const lineTo = m.to - matchingLine.from;
      let previewText = matchingLine.text.slice(Math.max(0, lineFrom - 20), lineTo + 100);
      if (m.from - matchingLine.from > 20) {
        previewText = '...' + previewText.slice(3);
      }

      return {
        ...m,
        field: field || '',
        matchingText,
        previewText,
        previewFrom: Math.min(lineFrom, 20),
        previewTo: Math.min(lineFrom, 20) + matchingText.length,
      }
    });
}

export function searchNotes<T extends NoteBase>(notes: T[], search?: string|null): NoteSearchResults<T> {
  if (!search || search.length < 3) {
    return [];
  }

  // perform search
  const resultList = notes.map(note => ({
    item: note,
    matches: searchField(note, search, 'title').concat(searchField(note, search, 'text')),
  }));

  // group results
  const groups = groupBy(resultList, 'item.parent');
  function collectChildren(parentId: string|null): NoteSearchResults<T> {
    return sortBy(groups[parentId as any] || [], 'order')
      .map(r => ({ ...r, children: collectChildren(r.item.id) }))
      .filter(r => r.matches.length > 0 || r.children.length > 0)
  }
  return collectChildren(null);
}


export function searchByDefinition(data: Record<string, any>, definition: FieldDefinition[], search?: string|null, path?: string) {
  if (!search || search.length < 3) {
    return [];
  }

  const results = [] as SearchResultMatch[];
  for (const fd of definition) {
    const fPath = (path || '') + ((!path || fd.id.startsWith('[')) ? '' : '.') + fd.id;
    if ([FieldDataType.STRING, FieldDataType.MARKDOWN, FieldDataType.COMBOBOX, FieldDataType.CVSS, FieldDataType.CWE].includes(fd.type)) {
      results.push(...searchField(data, search, fPath));
    } else if (fd.type === FieldDataType.LIST) {
      const list = get(data, fPath) as any[];
      if (Array.isArray(list)) {
        for (let i = 0; i < list.length; i++) {
          results.push(...searchByDefinition(data, [{...fd.items!, id: `[${i}]`}], search, fPath));
        }
      }
    } else if (fd.type === FieldDataType.OBJECT) {
      results.push(...searchByDefinition(data, fd.properties!, search, fPath));
    }
  }

  return results;
}


export function searchFindings(findings: PentestFinding[], projectType: ProjectType, search?: string|null): SearchResult<PentestFinding>[] {
  return findings.map(f => ({
    item: f,
    matches: searchByDefinition(f.data, projectType.finding_fields, search),
  })).filter(r => r.matches.length > 0);
}


export function searchSections(sections: ReportSection[], projectType: ProjectType, search?: string|null): SearchResult<ReportSection>[] {
  return projectType.report_sections.map(sd => {
    const section = sections.find(s => s.id === sd.id);
    if (!section) {
      return null;
    }
    return {
      item: section,
      matches: searchByDefinition(section.data, sd.fields, search),
    };
  }).filter(r => r && r.matches.length > 0) as SearchResult<ReportSection>[];
}
