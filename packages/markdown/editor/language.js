import { micromarkEventsToTree, parseMicromarkEvents } from "./micromark-utils";
import { LanguageSupport, Language, defineLanguageFacet, languageDataProp, indentNodeProp } from '@codemirror/language';
import {html} from "@codemirror/lang-html"
import {Prec} from "@codemirror/state";
import { keymap } from '@codemirror/view';
import { Parser, Tree, NodeSet, NodeType, parseMixed } from '@lezer/common';
import {styleTags, tags as t} from "@lezer/highlight"
import { markdownParser } from "..";
import { tags } from "./highlight";
import { insertNewlineContinueMarkup, deleteMarkupBackward, toggleStrong, toggleEmphasis } from "./commands";

const markdownLanguageFacet = defineLanguageFacet({block: {open: '<!--', close: '-->'}});

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
const nodeTypes = [
  'strong', 'strongSequence', 'emphasis', 'emphasisSequence', 'strikethrough', 'strikethroughSequence', 
  'codeText', 'codeFenced', 'table', 'blockQuote',
  'heading1', 'heading2', 'heading3', 'heading4', 'heading5', 'heading6',
  'link', 'image', 'resource', 'label', 'labelMarker', 'labelText',
  'inlineFootnote', 'textAttributes', 'templateVariable', 'todo',
  'htmlText', 'htmlFlow',
  'data', 'paragraph', 'content', 'document', 'lineEnding',
  'listOrdered', 'listUnordered', 'listItem', 'listItemPrefix', 'blockQuotePrefix', 'listItemMarker', 
];
const nodeSet = new NodeSet([NodeType.none].concat(nodeTypes.map((type, idx) => NodeType.define({id: idx + 1, name: type}))))
  .extend(markdownHighlighting)
  .extend(languageDataProp.add({ document: markdownLanguageFacet }))
  .extend(indentNodeProp.add({ document: () => null }));


function modifySyntaxTree(tree) {
  visitTree(tree);
  return tree;

  function visitTree(t) {
    for (const n of t) {
      visitNode(n);
      if ((n.children?.length || 0) > 0) {
        visitTree(n.children);
      }
    }
  }
  function visitNode(n) {
    // Add ListItem nodes
    if (['listOrdered', 'listUnordered'].includes(n.type)) {
      let listItems = [];
      let currentListItem = [];
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
    }
  }
}

function micromarkToLezerSyntaxTree(text, events) {
  const tree = modifySyntaxTree(micromarkEventsToTree(text, events));
  // console.log('markdown syntax tree', tree);
  
  function toBuffer(node) {
    const buffer = [];
    for (const c of node.children || []) {
      buffer.push(...toBuffer(c));
    }
    let nodeId = nodeSet.types.find(t => t.name === node.enter.type);
    if (node.type === 'atxHeading' && node.children.length >= 1 && node.children[0].type === 'atxHeadingSequence') {
      nodeId = nodeSet.types.find(t => t.name === 'heading' + node.children[0].text.length || 0);
    }
    
    buffer.push((nodeId || NodeType.none).id, node.enter.start.offset, node.enter.end.offset, 4 + buffer.length);
    return buffer;
  }

  return Tree.build({
    buffer: tree.length > 0 ? toBuffer({children: tree, enter: {type: 'document', start: tree[0].enter.start, end: tree.slice(-1)[0].enter.end}}) : [],
    nodeSet: nodeSet,
    topID: nodeSet.types.find(t => t.name === 'document').id,
  });
}


export function lezerSyntaxTreeParse() {
  const micromarkExtensions = this.data('micromarkExtensions') || [];
  this.Parser = parser;

  function parser(text) {
    const events = parseMicromarkEvents(text, {extensions: micromarkExtensions});
    return micromarkToLezerSyntaxTree(text, events);
  }
}


class BlockContext {
  constructor(parser, input, fragments, ranges) {
    this.parser = parser;
    this.input = input;
    this.fragments = fragments;
    this.ranges = ranges;
    this.stoppedAt = null;
  }
  
  advance() {
    // TODO: support incremental parsing: only parse current (and sourrounding?) blocks to increase performance
    // test performance:
    // * ~1ms: very short text
    // * 10-20ms: longer md document with many costructs
    // * 10-20ms: long text, no markup
    // * ~30-100ms: https://raw.githubusercontent.com/toptensoftware/markdowndeep/master/Backup/MarkdownDeepBenchmark/benchmark/markdown-example-long-2.text
    return markdownParser()
    .use(lezerSyntaxTreeParse)
    .parse(this.input.read(0, this.input.length));
  }

  get parsedPos() {
    return this.input.length;
  }

  stopAt(pos) {
    this.stoppedAt = pos;
  }

}


class MarkdownParser extends Parser {
  createParse(input, fragments, ranges) {
    const mdParser = new BlockContext(this, input, fragments, ranges);
    return parseMixed((node, input) => {
      if (['htmlText', 'htmlFlow'].includes(node.name)) {
        return {parser: htmlLanguage.language.parser, overlay: [{from: node.from, to: node.to}]}
      }
      return null;
    })(mdParser, input, fragments, ranges);
  }
}

const htmlLanguage = html({matchClosingTags: false});

export const markdownLanguage = new Language(
  markdownLanguageFacet, 
  new MarkdownParser()
);

export function markdown() {
  return new LanguageSupport(markdownLanguage, [
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
