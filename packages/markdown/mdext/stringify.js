import { htmlVoidElements } from 'html-void-elements'
import { html } from 'property-information'
import { stringifyEntities } from 'stringify-entities'
import { handle } from '../node_modules/hast-util-to-html/lib/handle/index'
import { all } from '../node_modules/hast-util-to-html/lib/index'


export function rehypeStringify() {
  this.compiler = toHtml;
}

export function toHtml(tree) {
  const state = {
    one,
    all,
    settings: {
      // Required to pass-through vue template variables.
      // In preview mode, rehype-sanitize already removed dangerous HTML at this point.
      allowDangerousHtml: true,  
      voids: htmlVoidElements,
      characterReferences: {},
      
    },
    schema: html,
    quote: '"',
    alternative: "'",
  }
  return state.one(
    Array.isArray(tree) ? {type: 'root', children: tree} : tree,
    undefined,
    undefined
  )
}

function one(node, index, parent) {
  return handleModified(node, index, parent, this);
}

function handleModified(node, index, parent, state) {
  if (node.type === 'text') {
    return text(node, index, parent, state);
  }
  return handle(node, index, parent, state);
}

export function text(node, _, parent, state) {
  // Check if content of `node` should be escaped.
  return parent &&
    parent.type === 'element' &&
    (parent.tagName === 'script' || parent.tagName === 'style')
    ? node.value
    : stringifyEntities(
        node.value,
        Object.assign({}, state.settings.characterReferences, {
          subset: ['<', '&', '{', '}']
        })
      )
}