import { micromarkEventsToTree, parseMicromarkEvents } from './micromark-utils.js';


function createBlockSeparator(pos) {
  return {
    type: 'annotatedTextBlockSeparator', 
    text: '', 
    children: [],
    enter: {
      type: 'annotatedTextBlockSeparator',
      start: pos,
      end: pos,
    },
    exit: {
      type: 'annotatedTextBlockSeparator',
      start: pos,
      end: pos,
    },
  };
}

export function extractLeafNodesFromMicromarkTree(tree, {interpretAsLeafNodes = [], interpretAsLeafNodesFns = {}, wrapTypesWithBlockSeparators = []}) {
  const leafNodes = [];
  collectLeafNodes(tree);
  return leafNodes;

  function collectLeafNodes(t) {
    for (const n of t) {
      const wrapWithSeparators = wrapTypesWithBlockSeparators.includes(n.type);
      if (wrapWithSeparators) {
        leafNodes.push(createBlockSeparator(n.enter.start));
      }

      if (n.children.length === 0 || interpretAsLeafNodes.includes(n.type) || interpretAsLeafNodesFns[n.type]?.(n)) {
        leafNodes.push(n);
      } else {
        collectLeafNodes(n.children);
      }

      if (wrapWithSeparators) {
        leafNodes.push(createBlockSeparator(n.exit.end));
      }
    }
  } 
}



function micromarkToAnnotatedText(text, events) {
  const tree = micromarkEventsToTree(text, events);
  // console.log('micromark tree', tree);

  // Add separators between blocks, such that blocks are always interpreted as separate
  for (let i = tree.length - 1; i >= 0; i--) {
    tree.splice(i, 0, createBlockSeparator(tree[i].enter.start));
  }

  // extract leaf nodes of tree => this is a sequence of all the text tokens
  const leafNodes = extractLeafNodesFromMicromarkTree(tree, {
    interpretAsLeafNodes: ['codeFenced', 'codeText', 'textAttributes', 'inlineFootnote', 'table', 'resource', 'templateVariable'],
    interpretAsLeafNodesFns: {
      'labelText': n => n.children.length === 0,
    },
    wrapTypesWithBlockSeparators: ['image'],
  });

  // console.log('annotatedText.leafNodes', leafNodes)

  // convert leaf nodes to annotatedText => either text or markup
  // TODO: support table caption in micromark (instead of mdast)
  const textTypes = ['data', 'lineEnding', 'lineEndingBlank'];
  const markupTypesInterpretAs = {
    'listItemMarker': '\n\n',
    'codeFenced': '\n\n',
    'annotatedTextBlockSeparator': '\n\n',
    'codeText': '`code`',
    'templateVariable': '`code`',
    'labelText': '`code`',
  };
  const annotatedText = [];
  for (const n of leafNodes) {
    if (n.type === 'lineEnding') {
      // Workaround for micromark bug: the end position of lineEnding elements is wrong (overlaps with next element)
      annotatedText.push({
        text: '\n',
        offset: n.enter.start.offset,
      });
    } else if (textTypes.includes(n.type)) {
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
  const micromarkExtensions = this.data('micromarkExtensions') || [];
  this.Parser = parser;

  function parser(text) {
    const events = parseMicromarkEvents(text, {extensions: micromarkExtensions});
    return micromarkToAnnotatedText(text, events);
  }
}