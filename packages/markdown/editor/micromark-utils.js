import {parse} from 'micromark/lib/parse.js';
import {preprocess} from 'micromark/lib/preprocess.js';
import {postprocess} from 'micromark/lib/postprocess.js';
import {assert} from '../mdext/helpers.js';


export function parseMicromarkEvents(text, config) {
  return postprocess(parse(config).document().write(preprocess()(text, undefined, true)));
}

export function micromarkEventsToTree(text, events) {
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
  return tree;
}
