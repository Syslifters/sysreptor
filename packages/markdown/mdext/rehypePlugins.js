import {visit} from 'unist-util-visit';

/**
 * Add target="_blank" to links.
 */
export function rehypeLinkTargetBlank() {
  return tree => {
    visit(tree, 'element', node => {
      if (node.tagName === 'a' && !(node.properties.href || '#').startsWith('#')) {
        node.properties.target = '_blank';
        node.properties.rel = 'nofollow noopener noreferrer';
      }
    });
  }
}

/**
 * Convert HTML attributes to inline CSS styles.
 */
export function rehypeConvertAttrsToStyle() {
  const convertAttrs = {
    'width': 'width', 
    'height': 'height'
  };

  return tree => {
    visit(tree, 'element', node => {
      for (const [attrName, styleName] of Object.entries(convertAttrs)) {
        if (node.properties[attrName]) {
          let style = (node.properties.style || '');
          if (style && style[style.length - 1] !== ';') {
            style += ';'
          }
          style += styleName + ':' + node.properties[attrName] + ';';
          node.properties.style = style;
          node.properties[attrName] = undefined;
        }
      }
    });
  }
}


function addClass(node, className) {
  if (!node.properties.className) {
    node.properties.className = [];
  }
  node.properties.className.push(className);
}

function splitCodeBlockIntoLines(codeBlockNode) {
  const childrenLines = [];
  let currentLine = [];
  processChildren(codeBlockNode.children)
  return childrenLines;

  function processChildren(children, classNames = []) {
    for (const c of children) {
      processNode(c, classNames);
    }
  }

  function processNode(node, classNames) {
    if (node.type === 'text') {
      for (const linePart of node.value.split(/(\n)/)) {
        if (linePart === '') { continue; }
        else if (linePart === '\n') {
          addLine();
        } else {
          addTextNode(linePart, classNames);
        }
      }
    } else if (node.type === 'element' && node.tagName === 'span') {
      processChildren(node.children, classNames.concat(node.properties.className || []));
    } else {
      // unexpected node: add on a own line
      console.error('rehypeCode: unexpected node', node);
      addLine(true);
      currentLine.push(node);
      addLine(true);
    }
  }

  function addTextNode(text, classNames) {
    const textNode = {type: 'text', value: text};
    if (classNames.length > 0) {
      currentLine.push({
        type: 'element',
        tagName: 'span',
        properties: {
          className: classNames,
        },
        children: [textNode]
      });
    } else {
      currentLine.push(textNode);
    }
  }

  function addLine(noNewline = false) {
    childrenLines.push({
      type: 'element',
      tagName: 'span',
      properties: {
        className: ['code-block-line'],
      },
      children: currentLine,
    });
    if (!noNewline) {
      childrenLines.push({
        type: 'text',
        value: '\n',
      });
    }
    currentLine = [];
  }
}

/**
 * Post process code blocks: add classes "code-block" or "code-inline".
 * Split code blocks into separate lines.
 * @returns 
 */
export function rehypeCode() {
  return tree => visit(tree, 'element', (node, index, parent) => {
    if (node.tagName === 'code') {
      if (parent.tagName === 'pre') {
        addClass(parent, 'code-block');

        // split code block into lines. Keep syntax highlighting.
        node.children = splitCodeBlockIntoLines(node);
      } else {
        addClass(node, 'code-inline');
      }
    }
  });
}


export function rehypeRewriteImageSources({rewriteImageSource}) {
  return tree => visit(tree, 'element', node => {
    if (node.tagName === 'img' && node.properties.src && rewriteImageSource) {
      node.properties.src = rewriteImageSource(node.properties.src);
    }
  });
}

