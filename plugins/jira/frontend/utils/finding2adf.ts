import { type PentestFinding, type FieldDefinition, FieldDataType, type ProjectType } from '#imports';
import type { ADFDocument, ADFNode } from "./md2adf";
import { markdownToADF } from './md2adf';
import { scoreFromVector, levelNameFromScore } from '@base/utils/cvss';


export function processFieldValue(value: any, definition: FieldDefinition, level: number = 1): ADFNode[] {
  if (value === null || value === undefined) {
    return [];
  }

  switch (definition.type) {
    case FieldDataType.MARKDOWN:
      return markdownToADF(value).content;
    
    case FieldDataType.CVSS: {
      // CVSS field: parse vector and format as "vector (score - level)"
      const score = scoreFromVector(value);
      const cvssLevel = levelNameFromScore(score);
      const scoreFormatted = score !== null ? score.toFixed(1) : '0.0';
      const text = `${value} (${scoreFormatted} - ${cvssLevel})`;
      return [{
        type: 'paragraph',
        content: [{ type: 'text', text }],
      }];
    }

    case FieldDataType.ENUM: {
      const choice = definition.choices?.find(c => c.value === value);
      const label = choice?.label || value;
      return [{
        type: 'paragraph',
        content: [{ type: 'text', text: label }],
      }];
    }

    case FieldDataType.JSON: {
      // JSON field: format as code block
      let jsonText;
      try {
        jsonText = JSON.stringify(JSON.parse(value), null, 2);
      } catch {
        jsonText = String(value);
      }
      return [{
        type: 'codeBlock',
        attrs: { language: 'json' },
        content: [{ type: 'text', text: jsonText }],
      }];
    }

    case FieldDataType.LIST: {
      // List field: process items based on item type
      if (!Array.isArray(value) || value.length === 0 || !definition.items) {
        return [];
      }

      if (definition.items.type === FieldDataType.OBJECT || 
          definition.items.type === FieldDataType.LIST || 
          definition.items.type === FieldDataType.MARKDOWN ||
          definition.items.type === FieldDataType.JSON) {
        // Complex items: render each with heading
        const nodes: ADFNode[] = [];
        for (let i = 0; i < value.length; i++) {
          const item = value[i];
          nodes.push({
            type: 'heading',
            attrs: { level: Math.min(level + 1, 6) },
            content: [{ type: 'text', text: `${definition.label || 'Item'} ${i + 1}` }],
          });
          nodes.push(...processFieldValue(item, definition.items, level + 1));
        }
        return nodes;
      } else {
        // Primitive items: render as bullet list
        const items = value
            .filter(item => item !== null && item !== undefined && item !== '')
            .map(item => ({
              type: 'listItem',
              content: processFieldValue(item, definition.items!, level + 1),
            }));
        if (items.length === 0) {
          return [];
        }
        return [{
          type: 'bulletList',
          content: items,
        }];
      }
    }

    case FieldDataType.OBJECT: {
      // Object field: process each property
      if (typeof value !== 'object' || !definition.properties) {
        return [];
      }

      const nodes: ADFNode[] = [];
      for (const nestedFieldDef of definition.properties) {
        const nestedValue = value[nestedFieldDef.id];
        if (nestedValue !== undefined && nestedValue !== null) {
          nodes.push({
            type: 'heading',
            attrs: { level: Math.min(level + 1, 6) },
            content: [{ type: 'text', text: nestedFieldDef.label || nestedFieldDef.id }],
          });
          nodes.push(...processFieldValue(nestedValue, nestedFieldDef, level + 1));
        }
      }
      return nodes;
    }
    
    case FieldDataType.STRING:
    case FieldDataType.COMBOBOX:
    case FieldDataType.DATE:
    case FieldDataType.CWE:
    case FieldDataType.NUMBER:
    case FieldDataType.BOOLEAN:
    case FieldDataType.USER:
    default:
      return [{
        type: 'paragraph',
        content: [{ type: 'text', text: String(value) }],
      }];
  }
}


export function findingToADF(finding: PentestFinding, projectType: ProjectType): ADFDocument {
  const content: ADFNode[] = [];

  // Process all top-level fields
  for (const fieldDef of projectType?.finding_fields || []) {
    if (['title'].includes(fieldDef.id)) {
      continue;
    }

    const fieldValue = finding.data?.[fieldDef.id];
    if (fieldValue === null || fieldValue === undefined) {
      continue;
    }

    // Add field label as heading
    content.push({
      type: 'heading',
      attrs: { level: 1 },
      content: [{ type: 'text', text: fieldDef.label || fieldDef.id }],
    });
    content.push(...processFieldValue(fieldValue, fieldDef));
  }
  
  return {
    version: 1,
    type: 'doc',
    content,
  };
}
