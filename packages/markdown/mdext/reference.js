import { visit } from 'unist-util-visit';
import { addClass } from './rehypePlugins';


export function rehypeReferenceLink() {
  return tree => visit(tree, 'element', (node, index, parent) => {
    if (node.tagName === 'a' && node.properties.href && node.properties.href.startsWith('#')) {
      node.tagName = 'ref';
      node.properties.to = node.properties.href.substring(1);
      delete node.properties.href;
    }
  });
}


export function rehypeReferenceLinkPreview({ rewriteReferenceLink = null }) {
  return tree => {
    let refNodes = [];
    let refTargets = {};

    // Collect references and elements that can be references
    visit(tree, 'element', (node, index, parent) => {
      if (node.tagName === 'a' && node.properties.href && node.properties.href.startsWith('#')) {
        refNodes.push(node);
      }
      if (node.properties.id) {
        refTargets[node.properties.id] = {node, index, parent};
      }
    });

    // Resolve references
    if (refNodes.length > 0) {
      for (const node of refNodes) {
        const refId = node.properties.href.substring(1);

        let refPreview = null;
        // Known reference target (e.g. other finding)
        if (!refPreview && rewriteReferenceLink) {
          refPreview = rewriteReferenceLink(refId);
        }

        // Local reference target (e.g. figure in same markdown field)
        if (!refPreview && refTargets[refId]) {
          if (refTargets[refId].node.tagName === 'img' && 
              refTargets[refId].parent.tagName === 'figure' && 
              refTargets[refId].parent.children.some(cn => cn.tagName === 'figcaption')) {
            refPreview = {
              title: `[Figure #${refId}]`,
            };
          }
          if (refTargets[refId].node.tagName === 'caption') {
            refPreview = {
              title: `[Table #${refId}]`,
            };
          }
        }

        // Unknown reference target
        if (!refPreview) {
          refPreview = {
            title: `[Reference to #${refId}]`,
          };
        }

        // Update reference node
        addClass(node, 'ref');
        if (refPreview.href) {
          node.properties.href = refPreview.href;
        }
        if (refPreview.title && node.children.length === 0) {
          node.children.push({type: 'text', value: refPreview.title});
        }
      }
    }

  }
}

