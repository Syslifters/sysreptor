import { markdownParser } from '@sysreptor/markdown';
import remarkParse from 'remark-parse';


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
      return { type: 'paragraph', content: convertChildren(node, originalMarkdown, false) };

    case 'text':
      return { type: 'text', text: node.value || '' };

    case 'heading':
      return {
        type: 'heading',
        attrs: { level: Math.min(Math.max(node.depth || 1, 1), 6) },
        content: convertChildren(node, originalMarkdown, false),
      };

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
          if (child.type !== 'paragraph' && child.type !== 'bulletList' && child.type !== 'orderedList') {
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

    case 'tableCell':
      const rawCellContent = convertChildren(node, originalMarkdown, true);
      // Wrap content in paragraph if not already
      const wrappedContent = rawCellContent.length === 0 
        ? [{ type: 'paragraph', content: [] }]
        : rawCellContent.every((n: ADFNode) => n.type === 'paragraph')
          ? rawCellContent
          : [{ type: 'paragraph', content: rawCellContent }];
      
      return {
        type: 'tableCell',
        attrs: {},
        content: wrappedContent,
      };

    case 'attributes':
      // Ignore
      return [];

    default:
      // For unsupported node types, use position-based slicing if available
      const text = getNodeText(node, originalMarkdown);
      if (blockContext) {
        return { type: 'paragraph', content: [{ type: 'text', text }] };
      }
      return { type: 'text', text };
  }
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

