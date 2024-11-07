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

export type NoteSearchResults<T extends NoteBase> = {
  note: T;
  matches: SearchResultMatch[];
  children: NoteSearchResults<T>;
}[];

function searchField(note: NoteBase, search: string, field: string): SearchResultMatch[] {
  const text = Text.of(get(note, field).split(/\r?\n/));
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
        field,
        matchingText,
        previewText,
        previewFrom: Math.min(lineFrom, 20),
        previewTo: Math.min(lineFrom, 20) + matchingText.length,
      }
    });
}

export function searchNotes<T extends NoteBase>(notes: T[], search?: string): NoteSearchResults<T> {
  if (!search || search.length < 3) {
    return [];
  }

  // perform search
  const resultList = notes.map(note => ({
    note,
    matches: searchField(note, search, 'title').concat(searchField(note, search, 'text')),
  }));

  // group results
  const groups = groupBy(resultList, 'note.parent');
  function collectChildren(parentId: string|null): NoteSearchResults<T> {
    return sortBy(groups[parentId as any] || [], 'order')
      .map(r => ({ ...r, children: collectChildren(r.note.id) }))
      .filter(r => r.matches.length > 0 || r.children.length > 0)
  }
  return collectChildren(null);
}
