import { micromarkEventsToTree, parseMicromarkEvents, type MicromarkTreeNode } from "./micromark-utils";
import { LanguageSupport, Language, defineLanguageFacet, languageDataProp, indentNodeProp, syntaxHighlighting } from '@codemirror/language';
import { html } from "@codemirror/lang-html"
import { Prec } from "@codemirror/state";
import { keymap } from '@codemirror/view';
import { Parser, Tree, NodeSet, NodeType, type Input, TreeFragment, type PartialParse, parseMixed, type SyntaxNode, IterMode } from '@lezer/common';
import { styleTags, tags as t } from "@lezer/highlight"
import { type Event } from 'micromark-util-types';
import { markdownParser } from "..";
import { markdownHighlightCodeBlocks, markdownHighlightStyle, tags } from "./highlight";
import { insertNewlineContinueMarkup, deleteMarkupBackward, toggleStrong, toggleEmphasis } from "./commands";
import type { Range } from "./codemirror-utils";

const markdownLanguageFacet = defineLanguageFacet({
  commentTokens: {
    block: {open: '<!--', close: '-->'}
  },
  closeBrackets: {
    brackets: ["(", "[", "{", "'", '"', "`", "_", "~"],
  },
});

const markdownHighlighting = styleTags({
  "strong/...": t.strong,
  "emphasis/...": t.emphasis,
  "strikethrough/...": t.strikethrough,
  "codeText/...": tags.inlinecode,
  "codeFenced/...": tags.codeblock,
  "table/...": tags.table,
  "blockQuote/...": t.quote,
  "heading1/...": t.heading1,
  "heading2/...": t.heading2,
  "heading3/...": t.heading3,
  "heading4/...": t.heading4,
  "heading5/...": t.heading5,
  "heading6/...": t.heading6,
  "link/...": t.link,
  "image/...": t.link,
  "textAttributes/...": t.link,
  "resource/...": t.url,
  "inlineFootnote/...": tags.footnote, 
  "templateVariable": tags.inlinecode,
  "todo/...": tags.todo,
});


enum MarkdownNodeType {
  // Node type names are the same as in micromark
  document = 1,

  content, paragraph, data, lineEnding, lineEndingBlank,
  strong, strongSequence,
  emphasis, emphasisSequence,
  strikethrough, strikethroughSequence,
  codeText, codeFenced,
  table, tableRow,
  blockQuote,
  heading1, heading2, heading3, heading4, heading5, heading6,
  link, image, resource,
  label, labelMarker, labelText,
  inlineFootnote, inlineFootnoteMarker, inlineFootnoteStartMarker, inlineFootnoteEndMarker,
  textAttributes, templateVariable, todo,
  htmlText, htmlFlow,
  listOrdered, listUnordered, listItem, listItemPrefix, blockQuotePrefix, listItemMarker, taskListCheck,
  reference, definition,
}
const nodeTypes = [NodeType.none].concat(
  Object.keys(MarkdownNodeType)
  .filter(name => !Number.parseInt(name))
  .map(name => NodeType.define({ id: MarkdownNodeType[name as any] as unknown as number, name })));
const nodeSet = new NodeSet(nodeTypes)
  .extend(markdownHighlighting)
  .extend(languageDataProp.add({ document: markdownLanguageFacet }))
  .extend(indentNodeProp.add({ document: () => null }));


function modifySyntaxTree(tree: MicromarkTreeNode[]) {
  visitTree(tree);
  return tree;

  function visitTree(t: MicromarkTreeNode[]) {
    for (const n of t) {
      visitNode(n);
      if ((n.children?.length || 0) > 0) {
        visitTree(n.children);
      }
    }
  }
  function visitNode(n: MicromarkTreeNode) {
    // Add ListItem nodes
    if (['listOrdered', 'listUnordered'].includes(n.type)) {
      let listItems = [] as any[];
      let currentListItem = [] as any[];
      for (const c of n.children) {
        if (c.type === 'listItemPrefix') {
          addListItem();
        }
        currentListItem.push(c);
      }
      addListItem();

      function addListItem() {
        if (currentListItem.length > 0) {      
          const info = {
            type: 'listItem',
            start: currentListItem[0].enter.start,
            end: currentListItem.slice(-1)[0].exit.end,
          };

          listItems.push({
            type: 'listItem', 
            enter: info,
            exit: info,
            children: currentListItem,
          });
          currentListItem = [];
        }
      }

      if (listItems.length > 0) {
        n.children = listItems;
      }
    } else if (n.type === 'atxHeading' && n.children.length >= 1 && n.children[0]!.type === 'atxHeadingSequence') {
      n.type = n.enter.type = n.exit.type = 'heading' + (n.children[0]!.text?.length || 0);
    } else if (n.type === 'setextHeading') {
      n.type = n.enter.type = n.exit.type = 'heading1';
    }
  }
}

function micromarkToLezerSyntaxTree(text: string, events: Event[]) {
  const mdTree = modifySyntaxTree(micromarkEventsToTree(text, events));
  
  function toBuffer(node: MicromarkTreeNode, buffer?: number[]) {
    buffer = buffer || [];
    const bufferLengthStart = buffer.length;
    for (const c of node.children || []) {
      toBuffer(c, buffer);
    }

    buffer.push(
      MarkdownNodeType[node.type as any] as number|undefined ?? NodeType.none.id, 
      node.enter.start.offset,
      node.enter.end.offset,
      4 + buffer.length - bufferLengthStart
    );
    return buffer;
  }

  const subtrees = mdTree.map(n => {
    const buffer = toBuffer(n);
    return Tree.build({
      buffer: buffer.slice(0, -4),
      nodeSet: nodeSet,
      topID: buffer.at(-4)!,
      start: n.enter.start.offset,
      length: n.enter.end.offset - n.enter.start.offset,
    });
  });
  
  const out = new Tree(
    nodeSet.types[MarkdownNodeType.document]!,
    subtrees,
    mdTree.map(n => n.enter.start.offset),
    mdTree.at(-1)?.exit.end.offset ?? 0,
  );
  return out;
}


export function lezerSyntaxTreeParse() {
  // @ts-ignore
  const self = this;

  const micromarkExtensions = self.data('micromarkExtensions') || [];
  self.Parser = parser;

  function parser(text: string) {
    const events = parseMicromarkEvents(text, {extensions: micromarkExtensions});
    return micromarkToLezerSyntaxTree(text, events);
  }
}


class BlockContext implements PartialParse {
  stoppedAt: number | null = null;

  constructor(
    readonly parser: MarkdownParser, 
    readonly input: Input, 
    readonly fragments: TreeFragment[], 
    readonly ranges: Range[],
  ) {}
  
  advance() {
    // Always handle the whole tree in a single call (not just single lines/blocks) because we don't support partial parsing / gaps in the tree.
    // We can still incrementally parse and update the syntax tree if possible

    // Try incremental parsing if possible
    try {
      const tree = this.reuseFragments();
      if (tree) {
        return tree;
      }
    } catch {}
    // Fallback: full re-parse of the whole document
    return this.performParse();
  }

  reuseFragments() {
    // On changes, the tree is split into tree fragments (which can be reused). 
    // Tree fragments do not contain changed ranges, instead they are split at change positions.
    // tree fragments format: fragment1(openStart=false,openEnd=true), change, fragment2(openStart=true,openEnd=false)
    //
    // The incremental parsing strategy works as follows:
    // 1. Identify unchanged fragments before and after the edit point
    // 2. For these fragments, verify that the markdown blocks surrounding the edit are structurally unchanged
    // 3. If they are unchanged, we can reuse those parts and only re-parse the edited block
    // 4. If the structure has changed, we fall back to full parsing

    let fragmentBefore: TreeFragment|null = null;
    let fragmentAfter: TreeFragment|null = null;

    // We only support 1 change at a time (at start or end or in the middle), because this is the most common case.
    // If more changes are present, re-parse the whole document.
    if (
      this.fragments.length === 2 &&
      !this.fragments[0]!.openStart && this.fragments[0]!.openEnd &&
      this.fragments[1]!.openStart && !this.fragments[1]!.openEnd
    ) {
      // Change in the middle of document
      fragmentBefore = this.fragments[0]!;
      fragmentAfter = this.fragments[1]!;
    } else if (this.fragments.length === 1 && this.fragments[0]!.openStart && !this.fragments[0]!.openEnd) {
      // Change at start of document
      fragmentAfter = this.fragments[0]!;
    } else if (this.fragments.length === 1 && !this.fragments[0]!.openStart && this.fragments[0]!.openEnd) {
      // Change at end of document
      fragmentBefore = this.fragments[0]!;
    } else {
      // Initial parse when document is first loaded
      // or multiple changed regions
      return null;
    }

    // Check if some blocks before and after the change are the same as before. 
    // This means it was just an inline change (e.g. inside a paragraph) that doesn't affect the structure of the document
    // and we can reuse unchanged blocks and only update the changed block.
    // If the document structure has changed, we need to re-parse the whole document.
    const oldBlocksBefore = fragmentBefore ? this.getMarkdownBlocks(fragmentBefore.tree, fragmentBefore.to + fragmentBefore.offset, 'before', 'exclude') : null;
    const oldBlocksAfter = fragmentAfter ? this.getMarkdownBlocks(fragmentAfter.tree, fragmentAfter.from + fragmentAfter.offset, 'after', 'exclude') : null;
    if (!oldBlocksBefore && !oldBlocksAfter) {
      return null;
    }

    // Check if changed blocks contain edge-case markdown constructs that cannot be parsed incrementally
    const oldBlocksChanged = this.getBlocksInRange(
      fragmentBefore?.tree || fragmentAfter!.tree, 
      oldBlocksBefore?.at(-1)?.to || 0,
      oldBlocksAfter?.at(0)?.from || this.input.length,
    );
    let needsFullReparse = false;
    oldBlocksChanged.forEach(b => b.toTree().iterate({ enter: n => {
      needsFullReparse ||= ([
        MarkdownNodeType.reference,   // links referencing definitions in other blocks cannot be resolved
        MarkdownNodeType.definition,  // changed definitions affect references in links
      ].includes(n.type.id)); 
    }}));
    if (needsFullReparse) {
      return null;
    }

    // Re-parse only a part of the document that is affected by the change (change + surrounding blocks)
    const reparseRange = {
      from: (fragmentBefore && oldBlocksBefore) ? oldBlocksBefore[0]!.from - fragmentBefore.offset : 0,
      to: (fragmentAfter && oldBlocksAfter) ? oldBlocksAfter.at(-1)!.to - fragmentAfter.offset : this.input.length,
    }
    const treeReparse = this.performParse(reparseRange);

    const newBlocksBefore = oldBlocksBefore ? this.getMarkdownBlocks(treeReparse, reparseRange.from, 'after', 'include') : null;
    const newBlocksAfter = oldBlocksAfter ? this.getMarkdownBlocks(treeReparse, reparseRange.to, 'before', 'include') : null;
    if (
      !this.compareBlocks(oldBlocksBefore, newBlocksBefore, fragmentBefore?.offset) ||
      !this.compareBlocks(oldBlocksAfter, newBlocksAfter, fragmentAfter?.offset)
    ) {
      // Surrounding blocks have changed. The change affects the document structure.
      // We need to re-parse the whole document.
      return null;
    }
    
    // Reuse unchanged blocks and only update the changed blocks
    const newBlocksChanged = this.getBlocksInRange(treeReparse, newBlocksBefore?.at(-1)?.to || 0, newBlocksAfter?.at(0)?.from || this.input.length);
    const reuseBlocksBefore = (fragmentBefore && oldBlocksBefore) ? this.getBlocksInRange(fragmentBefore.tree, 0, oldBlocksBefore.at(-1)!.to) : [];
    const reuseBlocksAfter = (fragmentAfter && oldBlocksAfter) ? this.getBlocksInRange(fragmentAfter.tree, oldBlocksAfter[0]!.from, fragmentAfter.tree.length) : [];

    const newTree = new Tree(
      nodeSet.types[MarkdownNodeType.document]!,
      reuseBlocksBefore
        .concat(newBlocksChanged)
        .concat(reuseBlocksAfter)
        .map(b => b.toTree()),
      reuseBlocksBefore.map(b => b.from - fragmentBefore!.offset)
        .concat(newBlocksChanged.map(b => b.from))
        .concat(reuseBlocksAfter.map(b => b.from - fragmentAfter!.offset)),
      this.input.length,
    );
    return newTree;
  }

  performParse(range?: {from: number, to: number}) {
    let tree = markdownParser()
      .use(lezerSyntaxTreeParse)
      .parse(this.input.read(range?.from ?? 0, range?.to ?? this.input.length)) as unknown as Tree;

    if (range) {
      // Fix positions of trees => relative to range.from
      tree = new Tree(
        tree.type,
        tree.children,
        tree.positions.map(p => p + range.from),
        tree.length + range.from,
      );
    }

    return tree;
  }

  getMarkdownBlocks(tree: Tree, pos: number, side: 'before'|'after', exact: 'include'|'exclude' = 'include', count: number = 1) {
    const isBefore = side === 'before';
    const includeExact = exact === 'include';

    const blocks: SyntaxNode[] = [];
    const cursor = tree.cursor(IterMode.IgnoreMounts | IterMode.IgnoreOverlays);
    for (
      let hasBlock = isBefore ? cursor.childBefore(pos) : cursor.childAfter(pos); 
      hasBlock && blocks.length < count; 
      hasBlock = isBefore ? cursor.prevSibling() : cursor.nextSibling()
    ) {
      if ([MarkdownNodeType.lineEnding, MarkdownNodeType.lineEndingBlank].includes(cursor.node.type.id)) {
        // Skip line endings because they are not actually blocks
        continue;
      }

      if (isBefore && includeExact ? cursor.to <= pos : cursor.to < pos) {
        blocks.unshift(cursor.node);
      } else if (!isBefore && includeExact ? cursor.from >= pos : cursor.from > pos) {
        blocks.push(cursor.node);
      }
    }
   
    if (blocks.length !== count) {
      return null;
    }
    return blocks;
  }

  getBlocksInRange(tree: Tree, from: number, to: number) {
    const mode = IterMode.IgnoreMounts | IterMode.IgnoreOverlays | IterMode.IncludeAnonymous;
    const cursor = tree.cursor(mode);
    const blocks: SyntaxNode[] = [];
    for (
      let hasBlock = cursor.enter(from, 1, mode); 
      hasBlock && cursor.to <= to; 
      hasBlock = cursor.nextSibling()
    ) {
      blocks.push(cursor.node);
    }
    return blocks;
  }

  compareBlocks(oldBlocks?: SyntaxNode[]|null, newBlocks?: SyntaxNode[]|null, fragmentOffset: number = 0) {
    if (!oldBlocks && !newBlocks) {
      return true;
    }
    if (!oldBlocks || !newBlocks) {
      return false;
    }

    const oldFormatted = oldBlocks.flatMap(b => {
      const out: number[] = [];
      b.toTree().iterate({ enter: n => { out.push(n.type.id, n.from + b.from - fragmentOffset, n.to + b.from - fragmentOffset) } });
      return out;
    });
    const newFormatted = newBlocks.flatMap(b => {
      const out: number[] = [];
      b.toTree().iterate({ enter: n => { out.push(n.type.id, n.from + b.from, n.to + b.from) } });
      return out;
    });

    if (oldFormatted.length !== newFormatted.length) {
      return false;
    }
    for (let i = 0; i < oldFormatted.length; i++) {
      if (oldFormatted[i] !== newFormatted[i]) {
        return false;
      }
    }
    
    return true;
  }

  get parsedPos() {
    return 0;
  }

  stopAt(_pos: number) {
    // partial parsing is not supported
  }

}


class MarkdownParser extends Parser {
  createParse(input: Input, fragments: TreeFragment[], ranges: Range[]) {
    // fragments: tree fragments that can be reused by incremental parsing
    // ranges: list of ranges to parse. Related to partial parsing, not relevant for incremental parsing.
    const mdParser = new BlockContext(this, input, fragments, ranges);
    return parseMixed((node, input) => {
      if ([MarkdownNodeType.htmlText, MarkdownNodeType.htmlFlow].includes(node.type.id)) {
        return {parser: htmlLanguage.language.parser, overlay: [{from: node.from, to: node.to}]}
      }
      return null;
    })(mdParser, input, fragments, ranges);
  }
}

const htmlLanguage = html({ matchClosingTags: false });
export const markdownLanguage = new Language(
  markdownLanguageFacet,
  new MarkdownParser(),
);

export function markdown() {
  return new LanguageSupport(markdownLanguage, [
    syntaxHighlighting(markdownHighlightStyle),
    markdownHighlightCodeBlocks,
    Prec.high(keymap.of([
      {key: 'Enter', run: insertNewlineContinueMarkup},
      {key: 'Backspace', run: deleteMarkupBackward},
    ])),
    keymap.of([
      {key: 'Mod-b', run: toggleStrong},
      {key: 'Mod-i', run: toggleEmphasis},
    ])
  ]);
}
