
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypeRaw from 'rehype-raw';
import remarkStringify from 'remark-stringify';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { merge } from 'lodash';
import 'highlight.js/styles/default.css';

import { remarkFootnotes, remarkToRehypeHandlersFootnotes, rehypeFootnoteSeparator, rehypeFootnoteSeparatorPreview } from './mdext/footnotes.js';
import { remarkStrikethrough, remarkTaskListItem } from './mdext/gfm.js';
import { rehypeConvertAttrsToStyle, rehypeLinkTargetBlank, rehypeRewriteImageSources, rehypeRewriteFileLinks, rehypeTemplates, rehypeRawFixSelfClosingTags } from './mdext/rehypePlugins.js';
import { remarkAttrs, remarkToRehypeAttrs } from './mdext/attrs.js';
import { remarkFigure, remarkToRehypeHandlersFigure } from './mdext/image.js';
import { remarkTables, remarkTableCaptions, remarkToRehypeHandlersTableCaptions, rehypeTableCaptions } from './mdext/tables.js';
import { rehypeReferenceLink, rehypeReferenceLinkPreview } from './mdext/reference.js';
import { annotatedTextParse } from './editor/annotatedtext.js';
import { remarkTemplateVariables } from './mdext/templates.js';
import { remarkTodoMarker } from './mdext/todo.js';
import { rehypeHighlightCode } from './mdext/codeHighlight.js';
import { modifiedCommonmarkFeatures } from './mdext/modified-commonmark.js';


const rehypeSanitizeSchema = merge({}, defaultSchema, {
  allowComments: true,
  clobberPrefix: null,
  tagNames: ['footnote', 'template', 'ref', 'pagebreak', 'markdown', 'u'].concat(defaultSchema.tagNames),
  attributes: {
    '*': ['className', 'style', 'data*', 'v-if', 'v-for', 'v-bind', 'v-on'].concat(defaultSchema.attributes['*']),
    'a': ['download'].concat(defaultSchema.attributes['a']),
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

export function renderMarkdownToHtml(text, {preview = false, rewriteFileSource = null, rewriteReferenceLink = null} = {}) {
  const md = markdownParser()
      .use(remarkParse)
      .use(remarkRehype, { 
        allowDangerousHtml: true, 
        footnoteLabelTagName: 'h4',
        handlers: {
          ...(preview ? {} : remarkToRehypeHandlersFootnotes),
          ...remarkToRehypeHandlersFigure,
          ...remarkToRehypeHandlersTableCaptions,
          ...remarkToRehypeAttrs,
        }
      })
      .use(rehypeTableCaptions)
      .use(rehypeHighlightCode)
      .use(rehypeRawFixSelfClosingTags)
      .use(rehypeRaw)
      .use(rehypeConvertAttrsToStyle)
      .use(rehypeTemplates)
      .use(preview ? rehypeFootnoteSeparatorPreview : rehypeFootnoteSeparator)
      .use(preview ? rehypeReferenceLinkPreview : rehypeReferenceLink, {rewriteReferenceLink})
      .use(rehypeRewriteImageSources, {rewriteImageSource: rewriteFileSource})
      .use(rehypeRewriteFileLinks, {rewriteFileUrl: rewriteFileSource})
      .use(rehypeLinkTargetBlank)
      .use(rehypeSanitize, rehypeSanitizeSchema)
      .use(rehypeStringify);

    // const mdAst = md.parse(text);
    // console.log('MarkdownAST', mdAst);
    // const rehypeAst = md.runSync(mdAst);
    // console.log('RehypeAST', rehypeAst);
    // const mdHtml = md.stringify(rehypeAst);
    // console.log('HTML', mdHtml);
    const mdHtml = md.processSync(text).value;
    return mdHtml;
}


export function markdownToAnnotatedText(text) {
  const md = markdownParser()
    .use(annotatedTextParse);
  const at = md.parse(text);
  // console.log('AnnotatedText', at);
  return at;
}
