import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeRemark from 'rehype-remark';
import remarkStringify from 'remark-stringify';
import rehypeParse from 'rehype-parse';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { defaultHandlers as defaultHandlersToMdast, defaultNodeHandlers as defaultNodeHandlersToMdast } from 'hast-util-to-mdast';
import { merge } from 'lodash-es';

import { remarkFootnotes, remarkToRehypeHandlersFootnotes, remarkToRehypeHandersFootnotesPreview, rehypeFootnoteSeparator, rehypeFootnoteSeparatorPreview } from './footnotes';
import { remarkStrikethrough, remarkTaskListItem } from './gfm';
import { rehypeConvertAttrsToStyle, rehypeLinkTargetBlank, rehypeRewriteFileUrls, rehypeTemplates, rehypeRawFixSelfClosingTags, rehypeRawFixPassthroughStitches, rehypeAnnotateMarkdownPositions } from './rehypePlugins';
import { remarkAttrs, remarkToRehypeAttrs } from './attrs';
import { remarkFigure, remarkToRehypeHandlersFigure } from './image';
import { remarkTables, remarkTableCaptions, remarkToRehypeHandlersTableCaptions, rehypeTableCaptions } from './tables';
import { rehypeReferenceLink, rehypeReferenceLinkPreview } from './reference';
import { annotatedTextParse } from '../editor/annotatedtext';
import { remarkTemplateVariables, remarkToRehypeTemplateVariables, rehypeTemplateVariables } from './templates';
import { remarkTodoMarker } from './todo';
import { rehypeHighlightCode } from './codeHighlight';
import { modifiedCommonmarkFeatures } from './modified-commonmark';
import { rehypeStringify } from './stringify';

const allClasses = ['className', /^.*$/];
const rehypeSanitizeSchema = merge({}, defaultSchema, {
  allowComments: true,
  clobberPrefix: null,
  tagNames: [
    // Custom components
    'footnote', 'template', 'ref', 'pagebreak', 'markdown', 'mermaid-diagram', 'qrcode',
    // Regular HTML tags not included in default schema
    'figure', 'figcaption', 'caption', 'mark', 'u',
    'abbr', 'bdo', 'cite', 'dfn', 'time', 'var', 'wbr',
  ].concat(defaultSchema.tagNames),
  attributes: {
    '*': ['className', 'style', 'data*', 'v-if', 'v-else-if', 'v-else', 'v-for', 'v-bind', 'v-on', 'v-show', 'v-pre', 'v-text'].concat(defaultSchema.attributes['*']),
    'a': ['download', 'target', 'rel', allClasses].concat(defaultSchema.attributes['a']),
    'img': ['loading'].concat(defaultSchema.attributes['img']),
    'code': [allClasses].concat(defaultSchema.attributes['code']),
    'h2': [allClasses].concat(defaultSchema.attributes['h2']),
    'ul': [allClasses].concat(defaultSchema.attributes['ul']),
    'ol': [allClasses].concat(defaultSchema.attributes['ol']),
    'li': [allClasses].concat(defaultSchema.attributes['li']),
    'section': [allClasses].concat(defaultSchema.attributes['section']),
    'input': ['checked'].concat(defaultSchema.attributes['input']),
    'ref': ['to', ':to'],
    'markdown': ['text', ':text'],
  }
});


export function markdownParser() {
  return unified()
    .use(modifiedCommonmarkFeatures)
    .use(remarkFootnotes)
    .use(remarkTables)
    .use(remarkTableCaptions)
    .use(remarkStrikethrough)
    .use(remarkTaskListItem)
    .use(remarkTemplateVariables)
    .use(remarkAttrs)
    .use(remarkFigure)
    .use(remarkTodoMarker);
}


/**
 * @param {string} html 
 * @returns {string}
 */
export function formatHtml(html) {
  return unified()
    .use(rehypeParse, { fragment: true })
    .use(rehypeStringify)
    .processSync(html)
    .value;
}


/**
 * @param {string} html
 * @returns {string}
 */
export function formatHtmlToMarkdown(html) {
  const md = markdownParser()
    .use(rehypeParse, { fragment: true })
    .use(rehypeRemark, {
      nodeHandlers: {
        ...defaultNodeHandlersToMdast,
        comment: () => {},
      },
      handlers: {
        ...defaultHandlersToMdast,
        a: (state, node) => {
          if (node.properties.href) {
            return defaultHandlersToMdast.a(state, node);
          }
          return state.all(node);
        }
      }
    })
    .use(remarkStringify)
  const text = md.processSync(html).value;
  return text;
}


/**
 * 
 * @param {string} text 
 * @returns {string}
 */
export function formatMarkdown(text) {
  const md = markdownParser()
    .use(remarkParse)
    .use(remarkStringify, {
      fence: '`',
      fences: true,
      bullet: '*',
      strong: '*',
      emphasis: '_',
    });
  return md.processSync(text).value;
}

/**
 * Render markdown text to HTML
 * @param {{text: string, preview?: boolean, referenceItems?: {id: string, href?: string, label?: string}[], rewriteFileUrlMap?: Record<string, string>, cacheBuster?: string}} options 
 * @returns {string}
 */
export function renderMarkdownToHtml({ text = '', preview = false, referenceItems = undefined, rewriteFileUrlMap = undefined, cacheBuster = undefined} = {}) {
  let md = markdownParser()
      .use(remarkParse)
      .use(remarkRehype, { 
        allowDangerousHtml: true, 
        footnoteLabelTagName: 'h4',
        handlers: {
          ...(preview ? remarkToRehypeHandersFootnotesPreview : remarkToRehypeHandlersFootnotes),
          ...remarkToRehypeHandlersFigure,
          ...remarkToRehypeHandlersTableCaptions,
          ...remarkToRehypeAttrs,
          ...remarkToRehypeTemplateVariables,
        },
      })
      .use(rehypeTableCaptions)
      .use(rehypeHighlightCode, { preview })
      .use(rehypeRawFixSelfClosingTags)
      .use(rehypeRaw, { passThrough: ['templateVariable']})
      .use(rehypeTemplates)
      .use(rehypeRawFixPassthroughStitches)
      .use(rehypeTemplateVariables, { preview })
      .use(rehypeConvertAttrsToStyle)
      .use(preview ? rehypeFootnoteSeparatorPreview : rehypeFootnoteSeparator)
      .use(preview ? rehypeReferenceLinkPreview : rehypeReferenceLink, { referenceItems })
    if (rewriteFileUrlMap) {
      md = md.use(rehypeRewriteFileUrls, { rewriteFileUrlMap, cacheBuster });
    }
    md = md.use(rehypeLinkTargetBlank)
    if (preview) {
      md = md
        .use(rehypeAnnotateMarkdownPositions)
        .use(rehypeSanitize, rehypeSanitizeSchema);
    }
    md = md.use(rehypeStringify);

    // Normalize linebreaks
    text = text.replace(/\r\n/g, '\n');

    // const mdAst = md.parse(text);
    // console.log('MarkdownAST', mdAst);
    // const rehypeAst = md.runSync(mdAst);
    // console.log('RehypeAST', rehypeAst);
    // const mdHtml = md.stringify(rehypeAst);
    // console.log('HTML', mdHtml);
    const mdHtml = md.processSync(text).value;
    return mdHtml;
}

/**
 * 
 * @param {string} text 
 * @returns {import('./editor/annotatedtext').AnnotatedText[]}
 */
export function markdownToAnnotatedText(text) {
  const md = markdownParser()
    .use(annotatedTextParse);
  const at = md.parse(text);
  // console.log('AnnotatedText', at);
  return at;
}


