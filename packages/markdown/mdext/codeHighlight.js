import { visit } from 'unist-util-visit';
import { toString } from 'hast-util-to-string';
import { camelCase } from 'lodash';
import { lowlight } from 'lowlight/lib/all'
import { unified } from 'unified';
import rehypeParse from 'rehype-parse';
import { addClass } from './rehypePlugins';


function getLanguage(node) {
  return (node.properties?.className || [])
    .filter(c => c.startsWith('language-'))
    .map(c => c.slice(9).toLowerCase())
    [0] || 'none';
}

function highlightSyntax(code, node) {
  const language = getLanguage(node);
  
  addClass(node, 'hljs');
  try {
    return lowlight.highlight(language, code);
  } catch (error) {
    if (!/Unknown language/.test(error)) {
      throw error;
    }
  }
  return {
    type: 'root',
    children: [{type: 'text', value: code}]
  };
}

function parseMeta(metaLine) {
  const meta = Object.fromEntries(
    Array.from(metaLine.matchAll(/(?<name>[a-zA-Z0-9\-]+)(?:="(?<value>[^"]+)")?/g))
      .map(m => [camelCase(m.groups.name), m.groups.value || null])
  );
  if (meta.highlightManual !== undefined) {
    meta.highlightManual = meta.highlightManual || '§';
  }
  if (meta.lineNumbers !== undefined) {
    meta.lineNumbers = Number.parseInt(meta.lineNumbers) || 1;
  }
  return meta;
}

function parseManualHighlightAreas(code, meta) {
  const highlightInfos = []
  if (!meta.highlightManual || meta.highlightManual.length !== 1) {
      return {code, highlightInfos};
  }

  const highlightMarkerRe = `\\${meta.highlightManual}[^\\${meta.highlightManual}\\R]*\\${meta.highlightManual}`;
  const highlightedAreaRe = new RegExp(`(${highlightMarkerRe})([^\\${meta.highlightManual}]*)(${highlightMarkerRe})`, 'g');
  const parts = code.split(highlightedAreaRe);
  let codeNew = '';
  for (let i = 0; i < parts.length; i += 4) {
    codeNew += parts[i];
    if (i + 3 < parts.length) {
      const highlightInfo = {
        startMarker: parts[i + 1].slice(1, parts[i + 1].length - 1),
        startMarkerPos: codeNew.length,
        endMarker: parts[i + 3].slice(1, parts[i + 3].length - 1),
        endMarkerPos: 0,
      };
      codeNew += parts[i + 2];
      highlightInfo.endMarkerPos = codeNew.length;
      highlightInfos.push(highlightInfo);
    }
  }

  return {code: codeNew, highlightInfos};
}


function splitTreeAtPosition(tree, splitPos) {
  return {
    ...tree,
    children: processChildren(tree.children, 0).flat(),
  }

  function processChildren(children, currentPos) {
    const childrenLeft = [];
    const childrenRight = [];

    for (const c of children) {
      for (const pc of processNode(c, currentPos)) {
        if (currentPos < splitPos) {
          childrenLeft.push(pc);
        } else {
          childrenRight.push(pc);
        }
        currentPos += toString(pc).length;
      }
    }
    return [childrenLeft, childrenRight];
  }

  function processNode(node, currentPos) {
    const nodeLength = toString(node).length;
    if (currentPos < splitPos && currentPos + nodeLength > splitPos) {
      if (node.type === 'text') {
        return [
          {...node, value: node.value.slice(0, splitPos - currentPos)},
          {...node, value: node.value.slice(splitPos - currentPos)},
        ];
      } else {
        const [childrenLeft, childrenRight] = processChildren(node.children, currentPos)
        return [
          {...node, children: childrenLeft},
          {...node, children: childrenRight},
        ];
      }
    }

    return [node];
  }
}


function wrapTreeAreas(tree, wrapInfos) {
  for (const wi of wrapInfos) {
    // Split highlighted HTML tree at the positions where manual highlight markers will be inserted
    tree = splitTreeAtPosition(tree, wi.startMarkerPos);
    tree = splitTreeAtPosition(tree, wi.endMarkerPos);
  }

  // Insert manual highlighting markers
  const children = [];
  for (let ci = 0, wii = 0, currentPos = 0; ci < tree.children.length; currentPos += toString(tree.children[ci]).length, ci++) {
    const c = tree.children[ci];
    let wi = wrapInfos[wii];

    if (wi && (currentPos >= wi.startMarkerPos && currentPos + toString(c).length <= wi.endMarkerPos)) {
      wi.children = (wi.children || []).concat([c]);

      if (currentPos + toString(c).length == wi.endMarkerPos) {
        visit(wi.markerTree, 'element', (node, index, parent) => {
          if (node.tagName === 'content-placeholder') {
            parent.children.splice(index, 1, ...wi.children);
          }
        });
        children.push(...wi.markerTree.children);
        wii += 1;
      }
    } else if (wi && (currentPos === wi.startMarkerPos && currentPos === wi.endMarkerPos)) {
      visit(wi.markerTree, 'element', (node, index, parent) => {
        if (node.tagName === 'content-placeholder') {
          parent.children.splice(index, 1);
        }
      });
      children.push(...wi.markerTree.children);
      children.push(c);
      wii += 1;
    } else {
      children.push(c);
    }
  }

  tree.children = children;
  return tree;
}


function applyManualHighlighting(tree, highlightInfos) {
  for (const hi of highlightInfos) {
    // Parse marker as HTML
    hi.markerTree = unified()
      .use(rehypeParse, {fragment: true})
      .parse((hi.startMarker || '<mark>') + '<content-placeholder />' + (hi.endMarker || '</mark>'))
  }

  return wrapTreeAreas(tree, highlightInfos);
}


function splitIntoLines(tree) {
  const lines = [];
  let currentPos = 0;
  for (const line of toString(tree).split('\n')) {
    lines.push({
      startMarkerPos: currentPos,
      endMarkerPos: currentPos + line.length,
      markerTree: {
        type: 'root',
        children: [
          {
            type: 'element',
            tagName: 'span',
            properties: {
              className: ['code-block-line'],
              dataLineNumber: lines.length + 1
            },
            children: [{type: 'element', tagName: 'content-placeholder', children: []}],
          }
        ]
      }
    });
    currentPos += line.length + 1;
  }
  
  return wrapTreeAreas(tree, lines);
}


export function rehypeHighlightCode() {
  return tree => visit(tree, 'element', (node, index, parent) => {
    if (node.tagName === 'code' && parent.tagName === 'pre') {
      addClass(parent, 'code-block');

      const meta = parseMeta(node.data?.meta || '');

      // Manual highlighting
      const {code, highlightInfos} = parseManualHighlightAreas(toString(node), meta);

      // Syntax highlighting
      let tree = highlightSyntax(code, node);

      // Add manual highighting
      if (highlightInfos.length > 0) {
        tree = applyManualHighlighting(tree, highlightInfos);
      }

      // Add line infos
      tree = splitIntoLines(tree);

      node.children = tree.children;
    } else if (node.tagName === 'code') {
      addClass(node, 'code-inline');
    }
  }); 
}
