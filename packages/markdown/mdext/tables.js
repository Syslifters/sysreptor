import { gfmTable } from 'micromark-extension-gfm-table';
import { gfmTableFromMarkdown, gfmTableToMarkdown } from 'mdast-util-gfm-table';
import { addRemarkExtension } from './helpers';
import { visit } from 'unist-util-visit';
import { all } from 'remark-rehype';
import { containerPhrasing } from 'mdast-util-to-markdown/lib/util/container-phrasing.js'


export function remarkTables() {
  addRemarkExtension(this, gfmTable, gfmTableFromMarkdown, gfmTableToMarkdown());
}


function tableCaptionFromMarkdown() {
  return {
    transforms: [transformTableCaption]
  };

  function transformTableCaption(tree) {
    visit(tree, (node, index, parent) => {
      if (node.type === 'table') {
        const captionBlock = parent.children[index + 1];
        if (captionBlock && captionBlock.type === 'paragraph' && captionBlock.children.length > 0 && captionBlock.children[0].type === 'text') {
          const captionText = captionBlock.children[0];
          let captionPrefixLength = 0;
          if (captionText.value.startsWith(':')) {
            captionPrefixLength = 1;
          } else if (captionText.value.startsWith('Table:')) {
            captionPrefixLength = 6;
          }

          
          if (captionPrefixLength) {
            const captionVal = captionText.value.slice(captionPrefixLength);
            const captionValTrimmed = captionVal.trimStart();
            captionPrefixLength += captionVal.length - captionValTrimmed.length;

            captionText.value = captionText.value.slice(captionPrefixLength);
            captionText.position.start.column += captionPrefixLength;
            captionText.position.start.offset += captionPrefixLength;

            // Mark block as table caption, but do not move caption into table (this is done when transforming to rehype)
            captionBlock.type = 'tableCaption';
          }
        }
      }
    });
  }
}


function tableCaptionToMarkdown() {
  return {
    handlers: {tableCaption},
  };

  function tableCaption(node, _, context, safeOptions) {
    const exit = context.enter('tableCaption');
    const subexit = context.enter('phrasing');
    const value = 'Table: ' + containerPhrasing(node, context, safeOptions);
    subexit();
    exit();
    return value;
  }
}


export function remarkTableCaptions() {
  addRemarkExtension(this, {}, tableCaptionFromMarkdown(), tableCaptionToMarkdown());
}


export const remarkToRehypeHandlersTableCaptions = {
  tableCaption(h, node) {
    return h(node, 'caption', all(h, node));
  }
};

export function rehypeTableCaptions() {
  return tree =>
    visit(tree, 'element', (node, index, parent) => {
      if (node.tagName === 'caption') {
        // Move table caption tag into HTML table
        const tableNode1 = parent.children[index - 1];
        const tableNode2 = parent.children[index - 2];
        if (tableNode1 && tableNode1.tagName === 'table') {
          tableNode1.children.push(node);
          parent.children.splice(index, 1);
        } else if (tableNode1 && tableNode1.type === 'text' && tableNode1.value === '\n' && tableNode2.tagName === 'table') {
          tableNode2.children.push(node);
          parent.children.splice(index, 1);
        }
      }
    });
}