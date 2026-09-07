import ZSchema from 'z-schema';
import { linter, type Diagnostic } from '@codemirror/lint';
import { syntaxTree } from '@codemirror/language';
import { EditorState, type Extension } from '@codemirror/state';
import type { SyntaxNode } from '@lezer/common';

const validator = ZSchema.create({ safe: true });

function decodePointerSegment(segment: string): string {
  return segment.replace(/~1/g, '/').replace(/~0/g, '~');
}

function parseJsonPointer(pointer: string): string[] {
  if (!pointer || pointer === '#' || pointer === '#/') {
    return [];
  }
  const normalized = pointer.startsWith('#/') ? pointer.slice(2)
    : pointer.startsWith('#') ? pointer.slice(1)
      : pointer.startsWith('/') ? pointer.slice(1)
        : pointer;
  if (!normalized) {
    return [];
  }
  return normalized.split('/').map(decodePointerSegment);
}

function normalizeErrorPath(path: string | Array<string | number> | undefined): string {
  if (!path) {
    return '#/';
  }
  if (Array.isArray(path)) {
    return '#/' + path.map(String).join('/');
  }
  return path;
}

function isValueNode(node: SyntaxNode): boolean {
  return !['{', '}', '[', ']', ':', ',', 'Property', 'PropertyName', 'JsonText'].includes(node.name);
}

function findObjectProperty(objectNode: SyntaxNode, key: string, state: EditorState): SyntaxNode|null {
  for (let child = objectNode.firstChild; child; child = child.nextSibling) {
    if (child.name !== 'Property') {
      continue;
    }
    const nameNode = child.getChild('PropertyName');
    if (!nameNode) {
      continue;
    }
    const name = state.doc.sliceString(nameNode.from, nameNode.to);
    const unquoted = name.length >= 2 && name.startsWith('"') ? JSON.parse(name) : name;
    if (unquoted === key) {
      return child;
    }
  }
  return null;
}

function findArrayItem(arrayNode: SyntaxNode, index: number): SyntaxNode|null {
  let i = 0;
  for (let child = arrayNode.firstChild; child; child = child.nextSibling) {
    if (!isValueNode(child)) {
      continue;
    }
    if (i === index) {
      return child;
    }
    i += 1;
  }
  return null;
}

function findJsonPointerRange(state: EditorState, pointer: string): { from: number; to: number } {
  const fallback = { from: 0, to: Math.min(1, state.doc.length) };
  const parts = parseJsonPointer(pointer);
  let node: SyntaxNode|null = syntaxTree(state).topNode;

  // Unwrap JsonText root
  if (node?.name === 'JsonText' && node.firstChild) {
    node = node.firstChild;
  }

  if (parts.length === 0) {
    return node ? { from: node.from, to: node.to } : fallback;
  }

  for (const part of parts) {
    if (!node) {
      return fallback;
    }
    if (node.name === 'Object') {
      const property = findObjectProperty(node, part, state);
      if (!property) {
        return { from: node.from, to: node.to };
      }
      // Prefer value node of the property
      let value: SyntaxNode|null = null;
      for (let child = property.firstChild; child; child = child.nextSibling) {
        if (isValueNode(child)) {
          value = child;
        }
      }
      node = value || property;
    } else if (node.name === 'Array') {
      const index = Number(part);
      if (!Number.isInteger(index) || index < 0) {
        return { from: node.from, to: node.to };
      }
      const item = findArrayItem(node, index);
      if (!item) {
        return { from: node.from, to: node.to };
      }
      node = item;
    } else {
      return { from: node.from, to: node.to };
    }
  }

  return node ? { from: node.from, to: node.to } : fallback;
}

function formatSchemaMessage(detailMessage?: string): string {
  return detailMessage
    ? `JSON schema: ${detailMessage}`
    : 'Does not match JSON schema';
}

export function jsonSchemaLinter(getSchema: () => Record<string, any>|null|undefined): Extension {
  return linter((view) => {
    const schema = getSchema();
    const text = view.state.doc.toString();
    if (!schema || !text) {
      return [];
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch {
      return [];
    }

    const result = validator.validate(parsed, schema);
    if (result.valid) {
      return [];
    }

    const details = result.err?.details || [];
    if (details.length === 0) {
      const range = findJsonPointerRange(view.state, '#/');
      return [{
        ...range,
        severity: 'error',
        message: formatSchemaMessage(),
      } satisfies Diagnostic];
    }

    return details.map((detail) => {
      const range = findJsonPointerRange(view.state, normalizeErrorPath(detail.path));
      return {
        ...range,
        severity: 'error' as const,
        message: formatSchemaMessage(detail.message),
      } satisfies Diagnostic;
    });
  }, { delay: 2000 });
}
