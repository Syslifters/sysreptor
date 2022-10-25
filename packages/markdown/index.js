
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeHighlight from 'rehype-highlight';
import rehypeStringify from 'rehype-stringify';
import rehypeRaw from 'rehype-raw';
import DOMPurify from 'dompurify';
import 'highlight.js/styles/default.css';

import { remarkFootnotes, remarkToRehypeHandlersFootnotes } from './mdext/footnotes.js';
import { remarkStrikethrough } from './mdext/gfm.js';
import { rehypeCode, rehypeConvertAttrsToStyle, rehypeLinkTargetBlank, rehypeRewriteImageSources } from './mdext/rehypePlugins.js';
import { remarkAttrs, remarkToRehypeAttrs } from './mdext/attrs.js';
import { remarkFigure, remarkToRehypeHandlersFigure } from './mdext/image.js';
import { remarkTables, remarkTableCaptions, remarkToRehypeHandlersTableCaptions, rehypeTableCaptions } from './mdext/tables.js';
import { annotatedTextParse } from './editor/annotatedtext.js';
import { remarkTemplateVariables } from './mdext/templates.js';
import { remarkTodoMarker } from './mdext/todo.js';
import remarkStringify from 'remark-stringify';


export function markdownParser() {
  // TODO: add plugins: 
  // * reference findings: #<finding-id>; current workaround [](#<finding-id>)
  // * enable autolinks?
  // write test cases for custom markdown extensions
  // * "text {{ var **with** _code_ `code` (which should not be interpreted as markdown) }} text {{ var with curly braces () => {"abc"} }} {no var}} {{ no var }"
  // * etc.
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
    .use(remarkStringify);
  return md.processSync(text);
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
      .use(rehypeHighlight, {subset: false, ignoreMissing: true})
      .use(rehypeRaw)
      .use(rehypeLinkTargetBlank)
      .use(rehypeCode)
      .use(rehypeRewriteImageSources, {rewriteImageSource})
      .use(rehypeStringify);

    // const mdAst = md.parse(text);
    // console.log('MarkdownAST', mdAst);
    // const rehypeAst = md.runSync(mdAst);
    // console.log('RehypeAST', rehypeAst);
    // const mdHtml = md.stringify(rehypeAst);
    // console.log('HTML', mdHtml);

    const mdHtml = md.processSync(text).value;
    return DOMPurify.sanitize(mdHtml, { ADD_TAGS: ['footnote'], ADD_ATTR: ['target', 'v-if'] });
}


export function markdownToAnnotatedText(text) {
  const md = markdownParser()
    .use(annotatedTextParse);
  const at = md.parse(text);
  // console.log('AnnotatedText', at);
  return at;
}
