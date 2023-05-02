import {EditorSelection} from "@codemirror/state"
import {syntaxTree} from "@codemirror/language"
import { markdownLanguage } from "./language";
import {linesInRange, getChildren, intersectsRange, getIntersectionNodes, moveRangeDelete, moveRangeInsert} from './codemirror-utils';


class Context {
  constructor(
    node,
    from,
    to,
    spaceBefore,
    spaceAfter,
    type,
    item
  ) {
    this.node = node;
    this.from = from;
    this.to = to;
    this.spaceBefore = spaceBefore;
    this.spaceAfter = spaceAfter;
    this.type = type;
    this.item = item;
  }

  blank(maxWidth = null, trailing = true) {
    let result = this.spaceBefore;
    if (this.node.name === "blockQuote") { 
      result += ">";
    }
    if (maxWidth !== null) {
      while (result.length < maxWidth) {
        result += " ";
      }
      return result;
    } else {
      for (let i = this.to - this.from - result.length - this.spaceAfter.length; i > 0; i--) {
        result += " ";
      }
      return result + (trailing ? this.spaceAfter : "");
    }
  }

  marker(doc, add) {
    let number = this.node.name == "listOrdered" ? String((+itemNumber(this.item, doc)[2] + add)) : ""
    return this.spaceBefore + number + this.type + this.spaceAfter
  }
}

function getContext(selectedNode, doc) {
  let nodes = []
  for (let cur = selectedNode; cur && cur.name != "document"; cur = cur.parent) {
    if (cur.name == "listItem" || cur.name == "blockQuote")
      nodes.push(cur)
  }
  let context = [];
  for (let i = nodes.length - 1; i >= 0; i--) {
    let node = nodes[i], match;
    let line = doc.lineAt(node.from), startPos = node.from - line.from;
    if (node.name == "blockQuote" && (match = /^[ \t]*>( ?)/.exec(line.text.slice(startPos)))) {
      context.push(new Context(node, startPos, startPos + match[0].length, "", match[1], ">", null));
    } else if (node.name == "listItem" && node.parent.name == "listOrdered" &&
               (match = /^([ \t]*)\d+([.)])([ \t]*)/.exec(line.text.slice(startPos)))) {
      let after = match[3], len = match[0].length
      if (after.length >= 4) { after = after.slice(0, after.length - 4); len -= 4 }
      context.push(new Context(node.parent, startPos, startPos + len, match[1], after, match[2], node));
    } else if (node.name == "listItem" && node.parent.name == "listUnordered" &&
               (match = /^([ \t]*)([-+*])([ \t]{1,4}\[[ xX]\])?([ \t]+)/.exec(line.text.slice(startPos)))) {
      let after = match[4], len = match[0].length
      if (after.length > 4) { after = after.slice(0, after.length - 4); len -= 4 }
      let type = match[2]
      if (match[3]) type += match[3].replace(/[xX]/, ' ')
      context.push(new Context(node.parent, startPos, startPos + len, match[1], after, type, node));
    }
  }
  return context
}

function itemNumber(item, doc) {
  return /^(\s*)(\d+)(?=[.)])/.exec(doc.sliceString(item.from, item.from + 10))
}

function renumberList(after, doc, changes, offset = 0) {
  for (let prev = -1, node = after;;) {
    if (node.name == "listItem") {
      let m = itemNumber(node, doc)
      let number = +m[2]
      if (prev >= 0) {
        if (number != prev + 1) return
        changes.push({from: node.from + m[1].length, to: node.from + m[0].length, insert: String(prev + 2 + offset)})
      }
      prev = number
    }
    let next = node.nextSibling
    if (!next) break
    node = next
  }
}

/// This command, when invoked in Markdown context with cursor
/// selection(s), will create a new line with the markup for
/// blockquotes and lists that were active on the old line. If the
/// cursor was directly after the end of the markup for the old line,
/// trailing whitespace and list markers are removed from that line.
///
/// The command does nothing in non-Markdown context, so it should
/// not be used as the only binding for Enter (even in a Markdown
/// document, HTML and code regions might use a different language).
export const insertNewlineContinueMarkup = ({state, dispatch}) => {
  let tree = syntaxTree(state), {doc} = state
  let dont = null, changes = state.changeByRange(range => {
    if (!range.empty || !markdownLanguage.isActiveAt(state, range.from)) return dont = {range}
    let pos = range.from, line = doc.lineAt(pos)
    let context = getContext(tree.resolveInner(pos, -1), doc)
    while (context.length && context[context.length - 1].from > pos - line.from) context.pop()
    if (!context.length) return dont = {range}
    let inner = context[context.length - 1]
    if (inner.to - inner.spaceAfter.length > pos - line.from) return dont = {range}

    let emptyLine = pos >= (inner.to - inner.spaceAfter.length) && !/\S/.test(line.text.slice(inner.to))
    // Empty line in list
    if (inner.item && emptyLine) {
      let next = context.length > 1 ? context[context.length - 2] : null
      let delTo, insert = ""
      if (next && next.item) { // Re-add marker for the list at the next level
        delTo = line.from + next.from
        insert = next.marker(doc, 1)
      } else {
        delTo = line.from + (next ? next.to : 0)
      }
      let changes = [{from: delTo, to: pos, insert}]
      if (inner.node.name == "listOrdered") {
        renumberList(inner.item, doc, changes, -2);
      }
      if (next && next.node.name == "listOrdered") {
        renumberList(next.item, doc, changes);
      }
      return {range: EditorSelection.cursor(delTo + insert.length), changes}
    }

    if (inner.node.name == "blockQuote" && emptyLine && line.from) {
      let prevLine = doc.lineAt(line.from - 1), quoted = />\s*$/.exec(prevLine.text)
      // Two aligned empty quoted lines in a row
      if (quoted && quoted.index == inner.from) {
        let changes = state.changes([{from: prevLine.from + quoted.index, to: prevLine.to},
                                     {from: line.from + inner.from, to: line.to}])
        return {range: range.map(changes), changes}
      }
    }

    let changes = []
    if (inner.node.name == "listOrdered") {
      renumberList(inner.item, doc, changes);
    }
    let continued = inner.item && inner.item.from < line.from;
    let insert = "";
    // If not dedented
    if (!continued || /^[\s\d.)\-+*>]*/.exec(line.text)[0].length >= inner.to) {
      for (let i = 0, e = context.length - 1; i <= e; i++) {
        insert += i == e && !continued ? context[i].marker(doc, 1)
          : context[i].blank(i < e ? context[i + 1].from - insert.length : null);
      }
    }
    let from = pos;
    while (from > line.from && /\s/.test(line.text.charAt(from - line.from - 1))) { 
      from--; 
    }
    insert = state.lineBreak + insert;
    changes.push({from, to: pos, insert});
    return {range: EditorSelection.cursor(from + insert.length), changes};
  })
  if (dont) return false
  dispatch(state.update(changes, {scrollIntoView: true, userEvent: "input"}))
  return true
}



function isMark(node) {
  return node.name == "blockQuotePrefix" || node.name == "listItemPrefix"
}

function contextNodeForDelete(tree, pos) {
  let node = tree.resolveInner(pos, -1), scan = pos
  if (isMark(node)) {
    scan = node.from
    node = node.parent
  }
  for (let prev; prev = node.childBefore(scan);) {
    if (isMark(prev)) {
      scan = prev.from
    } else if (prev.name == "listOrdered" || prev.name == "listUnordered") {
      node = prev.lastChild
      scan = node.to
    } else {
      break
    }
  }
  return node;
}


/// This command will, when invoked in a Markdown context with the
/// cursor directly after list or blockquote markup, delete one level
/// of markup. When the markup is for a list, it will be replaced by
/// spaces on the first invocation (a further invocation will delete
/// the spaces), to make it easy to continue a list.
///
/// When not after Markdown block markup, this command will return
/// false, so it is intended to be bound alongside other deletion
/// commands, with a higher precedence than the more generic commands.
export const deleteMarkupBackward = ({state, dispatch}) => {
  let tree = syntaxTree(state)
  let dont = null, changes = state.changeByRange(range => {
    let pos = range.from, {doc} = state
    if (range.empty && markdownLanguage.isActiveAt(state, range.from)) {
      let line = doc.lineAt(pos)
      let context = getContext(contextNodeForDelete(tree, pos), doc)
      if (context.length) {
        let inner = context[context.length - 1]
        let spaceEnd = inner.to - inner.spaceAfter.length + (inner.spaceAfter ? 1 : 0)
        // Delete extra trailing space after markup
        if (pos - line.from > spaceEnd && !/\S/.test(line.text.slice(spaceEnd, pos - line.from)))
          return {range: EditorSelection.cursor(line.from + spaceEnd),
                  changes: {from: line.from + spaceEnd, to: pos}}
        if (pos - line.from == spaceEnd &&
            // Only apply this if we're on the line that has the
            // construct's syntax, or there's only indentation in the
            // target range
            (!inner.item || line.from <= inner.item.from || !/\S/.test(line.text.slice(0, inner.to)))) {
          let start = line.from + inner.from
          // Replace a list item marker with blank space
          if (inner.item && inner.node.from < inner.item.from && /\S/.test(line.text.slice(inner.from, inner.to))) {
            return {range, changes: {from: start, to: line.from + inner.to, insert: inner.blank(inner.to - inner.from)}};
          }
          // Delete one level of indentation
          if (start < pos) {
            return {range: EditorSelection.cursor(start), changes: {from: start, to: pos}};
          }
        }
      }
    }
    return dont = {range}
  })
  if (dont) return false
  dispatch(state.update(changes, {scrollIntoView: true, userEvent: "delete"}))
  return true
}


export function isTypeInSelection(state, type) {
  let tree = syntaxTree(state);
  return state.selection.ranges.some(range => getIntersectionNodes(tree, range, n => n.name === type).length > 0);
}


function toggleMarkdownAction({state, dispatch}, { isInSelection, enable, disable }) {
  const tree = syntaxTree(state);

  const changes = state.changeByRange(range => {
    if (!markdownLanguage.isActiveAt(state, range.from)) {
      return {range};
    }

    const foundNodes = getIntersectionNodes(tree, range, isInSelection);
    if (foundNodes.length > 0) {
      if (disable) {
        return disable(range, foundNodes);
      } else {
        return {range};
      }
    } else {
      if (enable) {
        return enable(range, tree);
      } else {
        return {range};
      }
    }
  });

  dispatch(state.update(changes, {scrollIntoView: true, userEvent: 'input'}));
  return true;
}


function toggleMarkerType({state, dispatch}, { type, markerTypes = [], startMarker = null, endMarker = null}) {
  return toggleMarkdownAction({state, dispatch}, {
    isInSelection: n => {
      return n.name === type || (n.name === 'data' && state.doc.sliceString(n.from, n.to) === startMarker + endMarker)
    },
    enable: (range) => {
      if (range.empty) {
        const insertText = 'text';
        return {
          range: EditorSelection.range(range.from + startMarker.length, range.to + startMarker.length + insertText.length),
          changes: [{from: range.from, insert: startMarker + insertText + endMarker}],
        };
      } else {
        // insert bold markers at start and end of selection
        return {
          range: EditorSelection.range(range.from + startMarker.length, range.to + startMarker.length),
          changes: [
            {from: range.from, insert: startMarker},
            {from: range.to, insert: endMarker},
        ]};
      }
    },
    disable: (range, foundNodes) => {
      // remove bold markers of all intersecting bold nodes
      const removeMarkers = foundNodes
        .flatMap(n => getChildren(n).concat(n))
        .filter(c => markerTypes.includes(c.name) || (c.name === 'data' && state.doc.sliceString(c.from, c.to) === startMarker + endMarker));
      let newRange = range;
      const changes = [];
      for (const cn of removeMarkers) {
        const change = {from: cn.from, to: cn.to};
        newRange = moveRangeDelete(newRange, range, change)
        changes.push(change);
      }
      return { range: newRange, changes };
    }
  });
}

export function toggleStrong({state, dispatch}) {
  return toggleMarkerType({state, dispatch}, {
    type: 'strong',
    markerTypes: ['strongSequence'],
    startMarker: '**',
    endMarker: '**'
  });
}

export function toggleEmphasis({state, dispatch}) {
  return toggleMarkerType({state, dispatch}, {
    type: 'emphasis',
    markerTypes: ['emphasisSequence'],
    startMarker: '_',
    endMarker: '_',
  });
}

export function toggleStrikethrough({state, dispatch}) {
  return toggleMarkerType({state, dispatch}, {
    type: 'strikethrough',
    markerTypes: ['strikethroughSequence'],
    startMarker: '~~',
    endMarker: '~~'
  });
}

export function toggleListUnordered({state, dispatch}) {
  return toggleMarkdownAction({state, dispatch}, {
    isInSelection: n => n.name === 'listUnordered',
    enable: (range, tree) => {
      // Add marker to start of each line
      // If line is a listItem of an listOrdered: replace the marker
      const changes = [];
      let newRange = range;
      for (const line of linesInRange(state.doc, range)) {
        const listItemNumber = getIntersectionNodes(tree, line, n => n.name === 'listItem' && n.parent.name === 'listOrdered')
          .flatMap(n => getChildren(n))
          .filter(n => n.name === 'listItemPrefix')
          .find(n => intersectsRange(line, n));
        
        if (listItemNumber) {
          const change = {from: listItemNumber.from, to: listItemNumber.to, insert: '* '};
          newRange = moveRangeInsert(moveRangeDelete(newRange, range, change), range, change);
          changes.push(change);
        } else {
          const change = {from: line.from, insert: '* '};
          newRange = moveRangeInsert(newRange, range, change);
          changes.push(change);
        }
      }
      return {
        range: newRange,
        changes,
      };
    },
    disable: (range, foundNodes) => {
      const removeMarkers = foundNodes
        .flatMap(n => getChildren(n))  // Get all listItems
        .filter(i => intersectsRange(range, i))  // Get selected listItems
        .flatMap(n => getChildren(n))
        .filter(n => n.name === 'listItemPrefix');
      let newRange = range;
      const changes = [];
      for (const cn of removeMarkers) {
        const change = {from: cn.from, to: cn.to};
        newRange = moveRangeDelete(newRange, range, change)
        changes.push(change);
      }
      return { range: newRange, changes };
    }
  });
}

export function toggleListOrdered({state, dispatch}) {
  return toggleMarkdownAction({state, dispatch}, {
    isInSelection: n => n.name === 'listOrdered',
    enable: (range, tree) => {
      // Add marker to start of each line
      // If line is a listItem of an listUnordered: replace the marker
      const changes = [];
      let newRange = range;
      let itemNumber = 0;
      for (const line of linesInRange(state.doc, range)) {
        itemNumber += 1;
        const listItemNumber =  itemNumber + '. ';

        const listItemBullet = getIntersectionNodes(tree, line, n => n.name === 'listItem' && n.parent.name === 'listUnordered')
          .flatMap(n => getChildren(n))
          .filter(n => n.name === 'listItemPrefix')
          .find(n => intersectsRange(line, n));
        
        if (listItemBullet) {
          const change = {from: listItemBullet.from, to: listItemBullet.to, insert: listItemNumber};
          newRange = moveRangeInsert(moveRangeDelete(newRange, range, change), range, change);
          changes.push(change);
        } else {
          const change = {from: line.from, insert: listItemNumber};
          newRange = moveRangeInsert(newRange, range, change);
          changes.push(change);
        }
      }
      return {
        range: newRange,
        changes,
      };
    },
    disable: (range, foundNodes) => {
      const removeMarkers = foundNodes
        .flatMap(n => getChildren(n))  // Get all listItems
        .filter(i => intersectsRange(range, i))  // Get selected listItems
        .flatMap(n => getChildren(n))
        .filter(n => n.name === 'listItemPrefix');
      let newRange = range;
      const changes = [];
      for (const cn of removeMarkers) {
        const change = {from: cn.from, to: cn.to};
        newRange = moveRangeDelete(newRange, range, change)
        changes.push(change);
      }
      return { range: newRange, changes };
    }
  });
}


export function toggleLink({state, dispatch}) {
  return toggleMarkdownAction({state, dispatch}, {
    isInSelection: n => n.name === 'link',
    enable: (range) => {
      return {
        range: EditorSelection.range(range.from + 1, range.to + 1),
        changes: [
          {from: range.from, insert: '['},
          {from: range.to, insert: '](' + (range.from === range.to ? 'https://' : state.doc.sliceString(range.from, range.to)) + ')'},
        ]
      };
    },
    disable: (range, foundNodes) => {
      // Remove links only when a range is inside the link label
      const linksToRemove = foundNodes
        .filter(n => 
          getChildren(n)
          .flatMap(c => getChildren(c))
          .filter(c => c.name === 'labelText' && c.parent.name === 'label' && range.from >= c.from && range.to <= c.to)
          .length === 1)
        .flatMap(n => getChildren(n).flatMap(c => getChildren(c)))
        .filter(c => !(c.name === 'labelText' && c.parent.name === 'label'));
      const changes = [];
      let newRange = range;
      for (const n of linksToRemove) {
        const change = {from: n.from, to: n.to};
        newRange = moveRangeDelete(newRange, range, change);
        changes.push(change);
      }
      return {
        range: newRange,
        changes,
      };
    }
  });
}

export function insertCodeBlock({state, dispatch}) {
  return toggleMarkdownAction({state, dispatch}, {
    isInSelection: n => n.name === 'codeFenced',
    enable: (range) => {
      // insert "```\n" at the start of the first selected line and "\n```" at the end of the last selected line
      const codeBlockStart = state.lineBreak + '```' + state.lineBreak;
      const codeBlockEnd = state.lineBreak + '```';
      return {
        range: EditorSelection.range(range.from + codeBlockStart.length, range.to + codeBlockStart.length),
        changes: [
          {from: state.doc.lineAt(range.from).from, insert: codeBlockStart},
          {from: state.doc.lineAt(range.to).to, insert: codeBlockEnd},
        ],
      };
    },
  })
}

export function insertTable({state, dispatch}) {
  return toggleMarkdownAction({state, dispatch}, {
    isInSelection: n => n.name === 'table',
    enable: (range) => {
      return {
        range,
        changes: [{
          from: state.doc.lineAt(range.to).to, 
          insert: state.lineBreak +
                  '| Column1 | Column2 | Column3 |' + state.lineBreak +
                  '| ------- | ------- | ------- |' + state.lineBreak +
                  '| Text    | Text    | Text    |' + state.lineBreak + 
                  state.lineBreak,
        }],
      };
    }
  });
}

