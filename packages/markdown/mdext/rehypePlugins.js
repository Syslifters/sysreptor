import { visit } from 'unist-util-visit';

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
    'img': {
      'width': 'width', 
      'height': 'height',
    },
  };

  return tree => {
    visit(tree, 'element', node => {
      const attrMap = convertAttrs[node.tagName];
      if (!attrMap) {
        return;
      }
      for (const [attrName, styleName] of Object.entries(attrMap)) {
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


export function removeClass(node, className) {
  if (!node.properties.className) {
    return;
  }
  if (!Array.isArray(className)) {
    className = [className];
  }
  node.properties.className = node.properties.className.filter(c => !className.includes(c));
  if (node.properties.className.length === 0) {
    delete node.properties.className;
  }
}


/**
 * Rewrite image source to handle image fetching from markdown.
 * Images in markdown are referenced with a URL relative to the parent resource (e.g. "/images/name/image.png").
 */
export function rehypeRewriteFileUrls({ rewriteFileUrlMap, cacheBuster }) {
  function rewriteFileUrl(src) {
    for (const [oldPrefix, newPrefix] of Object.entries(rewriteFileUrlMap)) {
      if (src.startsWith(oldPrefix)) {
        return newPrefix + src.slice(oldPrefix.length) + (cacheBuster ? '?c=' + cacheBuster : '');
      }
    }
    return src;
  }

  return tree => visit(tree, 'element', node => {
    if (node.tagName === 'img' && node.properties.src) {
      node.properties.src = rewriteFileUrl(node.properties.src);
      node.properties.loading = 'lazy';
    }

    if (node.tagName === 'a' && node.properties.href && node.properties.href.startsWith('/files/')) {
      node.properties.href = rewriteFileUrl(node.properties.href);
      node.properties.download = true;
      addClass(node, ['file-download-preview']);
      node.children.unshift({
        type: 'element',
        tagName: 'i',
        properties: {
          className: ['v-icon', 'v-icon--size-default', 'mdi', 'mdi-file-download'],
        },
        children: [],
        position: node.position,
      });
    }
  });
}


export function rehypeTemplates() {
  return tree => visit(tree, 'element', node => {
    if (node.tagName === 'template') {
      node.tagName = 'span';
      node.children = node.content?.children || [];
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


export function rehypeRawFixPassthroughStitches() {
  return tree => visit(tree, 'comment', (node, index, parent) => {
    if (node.value?.stitch) {
      parent.children.splice(index, 1, node.value.stitch);
    }
  })
}


/**
 * Annotate markdown blocks with line numbers as HTML attributes
 */
export function rehypeAnnotateMarkdownPositions() {
  return tree => visit(tree, 'element', (node, _, parent) => {
    
    if (
      node.position && 
      // Only include top-level blocks and nested structures
      (parent.type === 'root' || (['li', 'tr', 'figure'].includes(node.tagName))) && 
      // Skip footnotes, because in the preview they are moved outside the document flow (rendered at the bottom)
      !node.properties?.id?.startsWith('user-content-fn')
    ) {
      node.properties = node.properties || {};
      node.properties.dataPosition = JSON.stringify(node.position);
    }
  });
}

