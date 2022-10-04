import {parse} from 'micromark/lib/parse.js';
import {preprocess} from 'micromark/lib/preprocess.js';
import {postprocess} from 'micromark/lib/postprocess.js';
import {assert} from './helpers.js';


function micromarkToAnnotatedText(text, events) {
  // console.log('micromark events', events);

  // build enter/exit tree of nested elements
  const tree = [];
  const stack = [];
  for (const [action, node, context] of events) {
    if (action === 'enter') {
      const treeNode = {
        enter: node,
        exit: null,  
        children: [],

        type: node.type,
        text: null,
      };
      if (stack.length > 0) {
        stack[stack.length - 1].children.push(treeNode);
      } else {
        tree.push(treeNode);
      }
      stack.push(treeNode);
    } else if (action === 'exit') {
      const treeNode = stack[stack.length - 1];
      assert(treeNode.type == node.type);

      treeNode.exit = node;
      treeNode.text = text.slice(treeNode.enter.start.offset, treeNode.exit.end.offset);
      stack.splice(stack.length - 1, 1);
    }
  }
  // console.log('micromark tree', tree);

  // extract leaf nodes of tree => this is a sequence of all the text tokens
  const leafNodes = [];
  const interpretTypesAsLeafNodes = ['codeFenced', 'codeText', 'textAttributes', 'inlineFootnote', 'table', 'resource', 'templateVariable'];
  function collectLeafNodes(t) {
    for (const n of t) {
      if (n.children.length === 0 || interpretTypesAsLeafNodes.includes(n.type)) {
        leafNodes.push(n);
      } else {
        collectLeafNodes(n.children);
      }
    }
  }
  collectLeafNodes(tree);


  // convert leaf nodes to annotatedText => either text or markup
  // TODO: support table caption in micromark (instead of mdast)
  const textTypes = ['data', 'lineEnding', 'lineEndingBlank'];
  const markupTypesInterpretAs = {
    'listItemMarker': '\n\n',
    'codeFenced': '\n\n',
    'codeText': '`code`',
    'templateVariable': '`code`',
  };
  const annotatedText = [];
  for (const n of leafNodes) {
    if (textTypes.includes(n.type)) {
      annotatedText.push({
        text: n.text,
        offset: n.enter.start.offset,
      });
    } else {
      annotatedText.push({
        markup: n.text,
        offset: n.enter.start.offset,
        interpretAs: markupTypesInterpretAs[n.type] || '',
      });
    }
  }
  return annotatedText;
}


export function annotatedTextParse() {
  // TODO: test with all markdown elements + combinations of elements
  const micromarkExtensions = this.data('micromarkExtensions') || [];
  this.Parser = parser;

  function parser(text) {
    const events = postprocess(parse({extensions: micromarkExtensions}).document().write(preprocess()(text, undefined, true)));
    return micromarkToAnnotatedText(text, events);
  }
}