import { markdownParser, remarkParse } from '@sysreptor/markdown';


export interface ADFNode {
  type: string;
  attrs?: Record<string, any>;
  content?: ADFNode[];
  text?: string;
  marks?: Array<{ type: string; attrs?: Record<string, any> }>;
}

export interface ADFDocument {
  version: 1;
  type: 'doc';
  content: ADFNode[];
}


export function mdastToADF(mdast: any, originalMarkdown?: string): ADFDocument {
  const content = convertNode(mdast, originalMarkdown);
  return {
    version: 1,
    type: 'doc',
    content: Array.isArray(content) ? content : [content],
  };
}

function convertNode(node: any, originalMarkdown?: string, blockContext: boolean = false): ADFNode | ADFNode[] {
  if (!node) {
    return [];
  }

  switch (node.type) {
    case 'root':
      return convertChildren(node, originalMarkdown, true);

    case 'paragraph':
      // Images are block nodes (mediaSingle) in ADF and cannot live inside a paragraph.
      // Split the paragraph around them.
      return groupInlineNodes(convertChildren(node, originalMarkdown, false), { keepEmpty: true });

    case 'image': {
      const url: string = node.url || '';
      if (!isSysreptorImageUrl(url) && !/^https?:\/\//i.test(url)) {
        // Relative URLs that are not SysReptor uploads cannot be resolved: keep markdown text
        return { type: 'text', text: getNodeText(node, originalMarkdown) };
      }
      const caption = (getPlainText(node) || node.alt || '').trim();
      const nodes: ADFNode[] = [{
        type: 'mediaSingle',
        attrs: { layout: 'center' },
        content: [{
          type: 'media',
          // SysReptor images (/images/name/...) are placeholders. The backend uploads them
          // as Jira attachments and replaces them with {type: 'file', id: <media-id>, collection: ''}.
          attrs: { type: 'external', url, ...(caption ? { alt: caption } : {}) },
        }],
      }];
      if (caption) {
        nodes.push({ type: 'paragraph', content: [{ type: 'text', text: caption, marks: [{ type: 'em' }] }] });
      }
      return nodes;
    }

    case 'text':
      return { type: 'text', text: node.value || '' };

    case 'heading': {
      const children = convertChildren(node, originalMarkdown, false);
      return [
        {
          type: 'heading',
          attrs: { level: Math.min(Math.max(node.depth || 1, 1), 6) },
          content: children.filter(n => !BLOCK_NODE_TYPES.has(n.type)),
        },
        ...children.filter(n => BLOCK_NODE_TYPES.has(n.type)),
      ];
    }

    case 'strong':
      return applyMark(convertChildren(node, originalMarkdown, false), { type: 'strong' });

    case 'emphasis':
      return applyMark(convertChildren(node, originalMarkdown, false), { type: 'em' });

    case 'delete':
      return applyMark(convertChildren(node, originalMarkdown, false), { type: 'strike' });

    case 'inlineCode':
    case 'inlineMath':
      return { type: 'text', text: node.value || '', marks: [{ type: 'code' }] };

    case 'code':
      return {
        type: 'codeBlock',
        attrs: node.lang ? { language: node.lang } : {},
        content: [{ type: 'text', text: node.value || '' }],
      };
    case 'math':
      return {
        type: 'codeBlock',
        attrs: { language: 'math' },
        content: [{ type: 'text', text: node.value || '' }],
      };

    case 'link':
      return applyMark(convertChildren(node, originalMarkdown, false), {
        type: 'link',
        attrs: { href: node.url || '' },
      });

    case 'list':
      return {
        type: node.ordered ? 'orderedList' : 'bulletList',
        content: convertChildren(node, originalMarkdown, true),
      };

    case 'listItem':
      return {
        type: 'listItem',
        content: convertChildren(node, originalMarkdown, true).map((child: ADFNode) => {
          // Wrap non-paragraph content in paragraphs
          if (!['paragraph', 'bulletList', 'orderedList', 'mediaSingle'].includes(child.type)) {
            return { type: 'paragraph', content: [child] };
          }
          return child;
        }),
      };

    case 'blockquote':
      // Blockquotes are only supported at top level in ADF
      return convertChildren(node, originalMarkdown, true);

    case 'break':
      return { type: 'hardBreak' };

    case 'table':
      return {
        type: 'table',
        content: convertChildren(node, originalMarkdown, true),
      };

    case 'tableRow':
      return {
        type: 'tableRow',
        content: convertChildren(node, originalMarkdown, true),
      };

    case 'tableCell': {
      const rawCellContent = convertChildren(node, originalMarkdown, true);
      // Wrap inline content in paragraphs, keep block nodes (paragraphs, images)
      const groupedContent = groupInlineNodes(rawCellContent);
      const wrappedContent = groupedContent.length === 0
        ? [{ type: 'paragraph', content: [] }]
        : groupedContent;

      return {
        type: 'tableCell',
        attrs: {},
        content: wrappedContent,
      };
    }

    case 'attributes':
      // Ignore
      return [];

    default: {
      // For unsupported node types, use position-based slicing if available
      const text = getNodeText(node, originalMarkdown);
      if (blockContext) {
        return { type: 'paragraph', content: [{ type: 'text', text }] };
      }
      return { type: 'text', text };
    }
  }
}

const BLOCK_NODE_TYPES = new Set([
  'paragraph', 'heading', 'mediaSingle', 'codeBlock', 'bulletList', 'orderedList', 'table',
]);

export function isSysreptorImageUrl(url: string): boolean {
  return url.startsWith('/images/name/');
}

function getPlainText(node: any): string {
  if (typeof node?.value === 'string') {
    return node.value;
  }
  return (node?.children || []).map(getPlainText).join('');
}

function trimEdgeWhitespace(nodes: ADFNode[]): ADFNode[] {
  const result = [...nodes];
  while (result.length > 0 && result[0]!.type === 'hardBreak') result.shift();
  while (result.length > 0 && result[result.length - 1]!.type === 'hardBreak') result.pop();
  if (result[0]?.type === 'text') {
    result[0] = { ...result[0], text: (result[0].text || '').replace(/^\s+/, '') };
  }
  const last = result.length - 1;
  if (result[last]?.type === 'text') {
    result[last] = { ...result[last], text: (result[last].text || '').replace(/\s+$/, '') };
  }
  return result.filter(n => n.type !== 'text' || n.text);
}

/**
 * Wrap runs of inline nodes in paragraphs and keep block nodes (e.g. mediaSingle) as they are.
 * Without block nodes in the input, the result is a single paragraph (unchanged behaviour).
 */
function groupInlineNodes(nodes: ADFNode[], options: { keepEmpty?: boolean } = {}): ADFNode[] {
  if (!nodes.some(n => BLOCK_NODE_TYPES.has(n.type))) {
    return (nodes.length > 0 || options.keepEmpty) ? [{ type: 'paragraph', content: nodes }] : [];
  }

  const result: ADFNode[] = [];
  let inline: ADFNode[] = [];
  const flush = () => {
    const content = trimEdgeWhitespace(inline);
    if (content.length > 0) {
      result.push({ type: 'paragraph', content });
    }
    inline = [];
  };
  for (const n of nodes) {
    if (BLOCK_NODE_TYPES.has(n.type)) {
      flush();
      result.push(n);
    } else {
      inline.push(n);
    }
  }
  flush();
  return result;
}

function getNodeText(node: any, originalMarkdown?: string): string {
  // Use position information to slice the original markdown
  if (originalMarkdown && node.position) {
    const start = node.position.start.offset;
    const end = node.position.end.offset;
    
    if (typeof start === 'number' && typeof end === 'number') {
      return originalMarkdown.slice(start, end);
    }
  }
  
  // Fallback: use value or serialize children
  if (node.value) {
    return node.value;
  }
  
  if (node.children && Array.isArray(node.children)) {
    return node.children.map((child: any) => getNodeText(child, originalMarkdown)).join('');
  }
  
  return '';
}

function convertChildren(node: any, originalMarkdown?: string, blockContext: boolean = false): ADFNode[] {
  if (!node.children || !Array.isArray(node.children)) {
    return [];
  }

  const result: ADFNode[] = [];
  for (const child of node.children) {
    const converted = convertNode(child, originalMarkdown, blockContext);
    if (Array.isArray(converted)) {
      result.push(...converted);
    } else if (converted) {
      result.push(converted);
    }
  }
  
  // Merge consecutive text nodes
  const merged: ADFNode[] = [];
  for (const node of result) {
    if (node.type === 'text' && merged.length > 0) {
      const lastNode = merged[merged.length - 1];
      if (lastNode && lastNode.type === 'text' && !lastNode.marks && !node.marks) {
        lastNode.text = (lastNode.text || '') + (node.text || '');
        continue;
      }
    }
    merged.push(node);
  }
  
  return merged;
}

function applyMark(nodes: ADFNode[], mark: { type: string; attrs?: Record<string, any> }): ADFNode[] {
  return nodes.map((node) => {
    if (node.type === 'text') {
      let marks = [...(node.marks || []), mark];
      const codeMark = marks.find(m => m.type === 'code');
      if (codeMark) {
        // Do not combine code marks with others
        marks = [codeMark];
      }
      return {
        ...node,
        marks,
      };
    }
    return node;
  });
}

export function markdownToADF(markdown: string): ADFDocument {
  try {
    const parser = markdownParser()
      .use(remarkParse)
    const mdast = parser.parse(markdown);
    return mdastToADF(mdast, markdown);
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to convert markdown to ADF:', error);
    // Fallback: return markdown as plain text paragraph
    return {
      version: 1,
      type: 'doc',
      content: [{
        type: 'paragraph',
        content: [{ type: 'text', text: markdown }],
      }],
    };
  }
}

