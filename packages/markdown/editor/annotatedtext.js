import { extractLeafNodesFromMicromarkTree, micromarkEventsToTree, parseMicromarkEvents } from './micromark-utils.js';



function micromarkToAnnotatedText(text, events) {
  // console.log('micromark events', events);
  const tree = micromarkEventsToTree(text, events);

  // extract leaf nodes of tree => this is a sequence of all the text tokens
  const interpretTypesAsLeafNodes = ['codeFenced', 'codeText', 'textAttributes', 'inlineFootnote', 'table', 'resource', 'templateVariable'];
  const leafNodes = extractLeafNodesFromMicromarkTree(tree, interpretTypesAsLeafNodes);

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
    const events = parseMicromarkEvents(text, {extensions: micromarkExtensions});
    return micromarkToAnnotatedText(text, events);
  }
}