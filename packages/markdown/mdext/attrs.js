import {codes} from 'micromark-util-symbol/codes.js';
import {factoryAttributes} from 'micromark-extension-directive/lib/factory-attributes.js';
import {parseEntities} from 'parse-entities';
import {visit} from 'unist-util-visit';
import { addRemarkExtension } from './helpers';


function attrsSyntax() {
  return {
    name: 'attrs',
    text: {
      [codes.leftCurlyBrace]: {
        tokenize: tokenizeAttributes,
      }
    }
  };

  function tokenizeAttributes(effects, ok, nok) {
    // Always a `{`
    return factoryAttributes(
      effects,
      ok,
      nok,
      'textAttributes',
      'textAttributesMarker',
      'textAttribute',
      'textAttributeId',
      'textAttributeClass',
      'textAttributeName',
      'textAttributeInitializerMarker',
      'textAttributeValueLiteral',
      'textAttributeValue',
      'textAttributeValueMarker',
      'textAttributeValueData'
    )
  }
};


function attrsFromMarkdown() {
  return {
    transforms: [transformAttributesAttachToElements],
    enter: {
      textAttributes: enterAttributes,
    },
    exit: {
      textAttributes: exitAttributes,
      textAttributeClassValue: exitAttributeClassValue,
      textAttributeIdValue: exitAttributeIdValue,
      textAttributeName: exitAttributeName,
      textAttributeValue: exitAttributeValue,
    }
  };

  function enterAttributes(token) {
    this.setData('directiveAttributes', []);
    this.enter({type: 'attributes', attrs: {}, attrsString: ''}, token);
    this.buffer();
  }

  function exitAttributeIdValue(token) {
    const list = this.getData('directiveAttributes');
    list.push(['id', parseEntities(this.sliceSerialize(token))])
  }

  function exitAttributeClassValue(token) {
    const list = this.getData('directiveAttributes');
    list.push(['class', parseEntities(this.sliceSerialize(token))])
  }

  function exitAttributeValue(token) {
    const list = this.getData('directiveAttributes');
    list[list.length - 1][1] = parseEntities(this.sliceSerialize(token))
  }

  function exitAttributeName(token) {
    // Attribute names in CommonMark are significantly limited, so character
    // references can’t exist.
    this.getData('directiveAttributes').push([this.sliceSerialize(token), ''])
  }

  function exitAttributes(token) {
    const cleaned = {};
    for (const attribute of this.getData('directiveAttributes')) {
      if (attribute[0] === 'class' && cleaned.class) {
        cleaned.class += ' ' + attribute[1];
      } else {
        cleaned[attribute[0]] = attribute[1];
      }
    }
  
    this.setData('directiveAttributes')
    this.resume(); // Drop EOLs

    const node = this.stack[this.stack.length - 1];
    node.attrs = cleaned;
    node.attrsString = this.sliceSerialize(token);
    this.exit(token);
  }

  function transformAttributesAttachToElements(tree) {
    // Attach attributes to elements or convert to text
    visit(tree, (node, index, parent) => {
      if (node.type === 'attributes') {
        const prevNode = index > 0 ? parent.children[index - 1] : null;
        if (prevNode && prevNode.type !== 'text') {
          // Attach attributes to previous element e.g. ![img](img.png){width="50%"}, **bold**{.styled}, but not "**bold** {.not-styled}"
          prevNode.data = {...prevNode.data, hProperties: node.attrs};
        } else if (['heading', 'tableCaption'].includes(parent.type)) {
          // Attach attributes to parent element e.g. "# Heading {#chapter-id}"
          parent.data = {...parent.data, hProperties: node.attrs};
        } else {
          // Could not attach to any node: convert attributes to text
          node.type = 'text';
          node.value = node.attrsString;
          delete node.attrs;
          delete node.attrsString;
        }
      }
    });
  }
}


function attrsToMarkdown() {
  return {
    handlers: {
      attributes
    }
  };

  function attributes(node, _, context) {
    const exit = context.enter('attributes');
    const value = node.attrsString || Object.entries(node.attrs).map(([k, v]) => {
      if (k === 'id') { return '#' + v }
      else if (k === 'class') { return v.split(' ').map(c => '.' + c).join(' ')}
      else { return `${k}=${v}`; }
    }).join(' ');
    exit();
    return value;
  }
}

export const remarkToRehypeAttrs = {
  attributes(h, node) {
    // Remove attributes nodes
    return null;
  }
}

export function remarkAttrs() {
  addRemarkExtension(this, attrsSyntax(), attrsFromMarkdown(), attrsToMarkdown());
}

