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


export function addClass(node, className) {
  if (!node.properties.className) {
    node.properties.className = [];
  }  
  if (Array.isArray(className)) {
    node.properties.className.push(...className);
  } else {
    node.properties.className.push(className);
  }
}


export function rehypeRewriteImageSources({rewriteImageSource}) {
  return tree => visit(tree, 'element', node => {
    if (node.tagName === 'img' && node.properties.src && rewriteImageSource) {
      node.properties.src = rewriteImageSource(node.properties.src);
    }
  });
}


export function rehypeRewriteFileLinks({ rewriteFileUrl }) {
  return tree => visit(tree, 'element', node => {
    if (node.tagName === 'a' && node.properties?.href?.startsWith('/files/') && rewriteFileUrl) {
      node.properties.href = rewriteFileUrl(node.properties.href);
      node.properties.download = true;
      addClass(node, ['file-download-preview', 'v-icon', 'mdi', 'mdi-file-download']);
    }
  });
}


export function rehypeTemplates() {
  return tree => visit(tree, 'element', node => {
    if (node.tagName === 'template') {
      node.children = node.content?.children || [];
      node.tagName = 'span';
    }
  })
}


/**
 * Replace self-closing tags with a combination of start and end tag.
 */
export function rehypeRawFixSelfClosingTags() {
  return tree => visit(tree, 'raw', (node) => {
    node.value = node.value.replaceAll(/<(?<tag>[a-zA-Z0-9-]+)(?<attrs>[^>]*)\/>/g, "<$<tag>$<attrs>></$<tag>>");
  });
}
