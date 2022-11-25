
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypeRaw from 'rehype-raw';
import xss from 'xss';
import 'highlight.js/styles/default.css';

import { remarkFootnotes, remarkToRehypeHandlersFootnotes, rehypeFootnoteSeparator, rehypeFootnoteSeparatorPreview } from './mdext/footnotes.js';
import { remarkStrikethrough } from './mdext/gfm.js';
import { rehypeConvertAttrsToStyle, rehypeLinkTargetBlank, rehypeRewriteImageSources } from './mdext/rehypePlugins.js';
import { remarkAttrs, remarkToRehypeAttrs } from './mdext/attrs.js';
import { remarkFigure, remarkToRehypeHandlersFigure } from './mdext/image.js';
import { remarkTables, remarkTableCaptions, remarkToRehypeHandlersTableCaptions, rehypeTableCaptions } from './mdext/tables.js';
import { annotatedTextParse } from './editor/annotatedtext.js';
import { remarkTemplateVariables } from './mdext/templates.js';
import { remarkTodoMarker } from './mdext/todo.js';
import { rehypeHighlightCode } from './mdext/codeHighlight.js';
import remarkStringify from 'remark-stringify';


export function markdownParser() {
  // TODO: add plugins: 
  // * reference findings: #<finding-id>; current workaround [](#<finding-id>)
  // * enable autolinks?
  return unified()
    .use(remarkFootnotes)
    .use(remarkTables)
    .use(remarkTableCaptions)
    .use(remarkStrikethrough)
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

export function renderMarkdownToHtml(text, {preview = false, rewriteImageSource = null} = {}) {
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
      .use(rehypeConvertAttrsToStyle)
      .use(rehypeTableCaptions)
      .use(preview ? rehypeFootnoteSeparatorPreview : rehypeFootnoteSeparator)
      .use(rehypeHighlightCode)
      .use(rehypeRaw)
      .use(rehypeLinkTargetBlank)
      .use(rehypeRewriteImageSources, {rewriteImageSource})
      .use(rehypeStringify);

    // const mdAst = md.parse(text);
    // console.log('MarkdownAST', mdAst);
    // const rehypeAst = md.runSync(mdAst);
    // console.log('RehypeAST', rehypeAst);
    // const mdHtml = md.stringify(rehypeAst);
    // console.log('HTML', mdHtml);

    const mdHtml = md.processSync(text).value;
    return xss(mdHtml, {
      allowCommentTag: true,
      css: false,
      allowList: {
        ...xss.whiteList,
        footnote: [],
        template: [],
      },
      onIgnoreTagAttr(tag, name, value, isWhiteAttr) {
        if (['id', 'class', 'style', 'v-if', 'v-for'].includes(name) || /^data-.*$/.test(name)) {
          return `${name}="${xss.escapeAttrValue(value)}"`;
        }
      },
    });
}


export function markdownToAnnotatedText(text) {
  const md = markdownParser()
    .use(annotatedTextParse);
  const at = md.parse(text);
  // console.log('AnnotatedText', at);
  return at;
}
