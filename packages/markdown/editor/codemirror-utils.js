import {EditorSelection} from "@codemirror/state"


export function linesInRange(doc, range) {
  const out = [];
  const startLine = doc.lineAt(range.from).number;
  const endLine = doc.lineAt(range.to).number;
  for (let i = startLine; i <= endLine; i++) {
    out.push(doc.line(i));
  }
  return out;
}

export function getChildren(n) {
  const out = [];
  for (let c = n.firstChild; c; c = c.nextSibling) {
    out.push(c);
  }
  return out;
}

export function intersectsRange(range, node) {
  return range.to >= node.from && node.to >= range.from;
}

export function iterateRange(tree, range, cb) {
  iterateChildren(tree.topNode);

  function iterateChildren(n) {
    if (!intersectsRange(range, n)) {
      return;
    }
    cb(n);
    for (const c of getChildren(n)) {
      iterateChildren(c);
    }
  }
}

export function getIntersectionNodes(tree, range, predicate) {
  const nodes = [];
  iterateRange(tree, range, n => {
    if (predicate(n)) {
      nodes.push(n);
    }
  });
  return nodes;
}

function clamp(val, min, max) {
  return Math.max(min, Math.min(max, val));
}


export function moveRangeDelete(moveRange, range, change) {
  const moveStart = clamp(change.from - range.from, change.from - change.to, 0);
  const moveEnd = clamp(change.from - range.to, change.from - change.to, 0);
  return EditorSelection.range(
    moveRange.from + moveStart,
    moveRange.to + moveEnd
  );
}


export function moveRangeInsert(moveRange, range, change) {
  return EditorSelection.range(
    moveRange.from + ((range.from > change.from) ? change.insert.length : 0),
    moveRange.to + ((range.to > change.from) ? change.insert.length : 0),
  );
}