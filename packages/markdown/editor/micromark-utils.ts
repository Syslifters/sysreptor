import { type Event } from 'micromark-util-types';
import { parse } from 'micromark/lib/parse';
import { preprocess } from 'micromark/lib/preprocess';
import { postprocess } from 'micromark/lib/postprocess';


export type MicromarkTreeNode = {
  enter: any,
  exit: any,
  children: MicromarkTreeNode[],
  type: string,
  text: string|null,
}


export function parseMicromarkEvents(text: string, options: any) {
  return postprocess(parse(options).document().write(preprocess()(text, undefined, true)));
}

export function micromarkEventsToTree(text: string, events: Event[]) {
  // console.log('micromark events', events);

  // build enter/exit tree of nested elements
  const tree = [] as MicromarkTreeNode[];
  const stack = [] as MicromarkTreeNode[];
  for (const [action, node, context] of events) {
    if (action === 'enter') {
      const treeNode = {
        enter: node,
        exit: null,  
        children: [],

        type: node.type,
        text: null,
      } as MicromarkTreeNode;
      if (stack.length > 0) {
        stack[stack.length - 1]!.children.push(treeNode);
      } else {
        tree.push(treeNode);
      }
      stack.push(treeNode);
    } else if (action === 'exit') {
      const treeNode = stack[stack.length - 1]!;

      treeNode.exit = node;
      treeNode.text = text.slice(treeNode.enter.start.offset, treeNode.exit.end.offset);
      stack.splice(stack.length - 1, 1);
    }
  }
  // console.log('micromark tree', tree);
  return tree;
}
