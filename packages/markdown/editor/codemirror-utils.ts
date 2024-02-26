import { EditorSelection, Line, SelectionRange, Text } from "@codemirror/state"
import { type SyntaxNode, Tree } from "@lezer/common";


export type Range = {
  from: number;
  to: number;
}


export function linesInRange(doc: Text, range: Range) {
  const out = [] as Line[];
  const startLine = doc.lineAt(range.from).number;
  const endLine = doc.lineAt(range.to).number;
  for (let i = startLine; i <= endLine; i++) {
    out.push(doc.line(i));
  }
  return out;
}

export function getChildren(n: SyntaxNode) {
  const out = [] as SyntaxNode[];
  for (let c = n.firstChild; c; c = c.nextSibling) {
    out.push(c);
  }
  return out;
}

export function intersectsRange(range: Range, node: SyntaxNode) {
  return range.to >= node.from && node.to >= range.from;
}

export function iterateRange(tree: Tree, range: Range, cb: (node: SyntaxNode) => void) {
  iterateChildren(tree.topNode);

  function iterateChildren(n: SyntaxNode) {
    if (!intersectsRange(range, n)) {
      return;
    }
    cb(n);
    for (const c of getChildren(n)) {
      iterateChildren(c);
    }
  }
}

export function getIntersectionNodes(tree: Tree, range: Range, predicate: (node: SyntaxNode) => boolean) {
  const nodes = [] as SyntaxNode[];
  iterateRange(tree, range, n => {
    if (predicate(n)) {
      nodes.push(n);
    }
  });
  return nodes;
}

function clamp(val: number, min: number, max: number) {
  return Math.max(min, Math.min(max, val));
}


export function moveRangeDelete(moveRange: Range, range: Range, change: {from: number, to: number}) {
  const moveStart = clamp(change.from - range.from, change.from - change.to, 0);
  const moveEnd = clamp(change.from - range.to, change.from - change.to, 0);
  return EditorSelection.range(
    moveRange.from + moveStart,
    moveRange.to + moveEnd
  );
}


export function moveRangeInsert(moveRange: SelectionRange, range: SelectionRange, change: {from: number, insert: string}) {
  return EditorSelection.range(
    moveRange.from + ((range.from > change.from) ? change.insert.length : 0),
    moveRange.to + ((range.to > change.from) ? change.insert.length : 0),
  );
}