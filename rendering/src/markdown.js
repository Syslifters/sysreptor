import MarkdownIt from 'markdown-it';
import { escapeHtml } from 'markdown-it/lib/common/utils';
import markdownItAttrs from 'markdown-it-attrs';
import markdownItFootnote from 'markdown-it-footnote';
import markdownItMultiMdTable from 'markdown-it-multimd-table';
import hljs from 'highlight.js';
import 'highlight.js/styles/default.css';


export function popAttr(attrs, name) {
  if (!attrs) {
    return undefined;
  }

  const valIdx = attrs.findIndex(a => a[0] === name);
  if (valIdx !== -1) {
    const val = attrs[valIdx][1];
    attrs.splice(valIdx, 1);
    return val;
  } else {
    return undefined;
  }
}


/**
 * Wrap images in a <figure> tag and add <figcaption>
 */
function imageCaptionPlugin(md) {
  const defaultImageRenderer = md.renderer.rules.image;
  md.renderer.rules.image = function(tokens, idx, options, env, self) {
    console.log('image caption', tokens[idx]);
    const token = tokens[idx];
    const img = defaultImageRenderer(tokens, idx, options, env, self);
    return '<figure>' + img + 
      ((token.children && token.children.length > 0) ? '<figcaption>' + self.renderInline(token.children) + '</figcaption>' : '') + 
    '</figure>';
  };
}

/**
 * Convert HTML attributes to inline CSS styles.
 */
function convertAttributesToStylesPlugin(md) {
  const convertAttrs = {
    'width': 'width', 
    'height': 'height'
  };

  function iterateTokens(tokens, fn) {
    for (const t of tokens || []) {
      fn(t);
      iterateTokens(t.children, fn);
    }
  }

  md.core.ruler.after('curly_attributes', 'attributes_to_style', (state) => {
    iterateTokens(state.tokens, t => {
      if (!t.attrs || t.attrs.length === 0) {
        return;
      }
      let style = popAttr(t.attrs, 'style') || '';
      for (const [attr_name, style_name] of Object.entries(convertAttrs)) {
        const attr_val = popAttr(t.attrs, attr_name);
        if (attr_val !== undefined) {
          if (style && style[style.length - 1] !== ';') {
            style += ';';
          }
          style += style_name + ':' + attr_val + ';';
        }
      }
      if (style) {
        t.attrs.push(['style', style]);
      }
    });
  });
}


/**
 * Add classes for markdown code blocks and inline code to better distinguish between them in CSS.
 */
function addCodeClasses(md) {
  function addClass(renderRuleName, className) {
    const defaultRenderer = md.renderer.rules[renderRuleName];
    md.renderer.rules[renderRuleName] = function(tokens, idx, options, env, self) {
      const codeToken = tokens[idx];
      let cls = popAttr(codeToken.attrs, 'class') || '';
      cls += ' ' + className;
      if (!codeToken.attrs) {
        codeToken.attrs = [];
      }
      codeToken.attrs.push(['class', cls]);

      return defaultRenderer(tokens, idx, options, env, self);
    }
  }

  addClass('code_block', 'code-block');
  addClass('code_inline', 'code-inline');
}


function footnotePlugin(md) {
  md.use(markdownItFootnote);

  // Disable block footnotes, support just inline footnotes
  md.block.ruler.disable('footnote_def');
  md.inline.ruler.disable('footnote_ref');
  
  if (!md.options.preview) {
    // Disable placing footnotes at the end of the markdown area. Positioning is handled by CSS.
    md.core.ruler.disable('footnote_tail');

    // Render footnotes as `<footnote>content</footnote>`
    md.renderer.rules.footnote_ref = (tokens, idx, options, env, self) => {
      const footnoteId = tokens[idx].meta.id;
      const footnoteContentTokens = env.footnotes.list[footnoteId].tokens;
      return `<footnote>${self.render(footnoteContentTokens)}</footnote>`
    }
  }
}


export function getMarkdownRenderer(preview = false) {
  return new MarkdownIt({
    html: true,
    breaks: false,
    linkify: false,
    typographer: false,
    highlight: function (code, language) {
      try {
        let highlightedCode = ''
        if (language && hljs.getLanguage(language)) {
            highlightedCode = hljs.highlight(code, { language }).value;
        } else {
            highlightedCode = hljs.highlightAuto(code).value;
        }
        return `<pre class="code-block ${escapeHtml(this.langPrefix + language)}"><code>${highlightedCode}</code></pre>`;
      } catch (_) {
        return '';
      }
    },
    preview: preview,
  })
  .use(imageCaptionPlugin)
  .use(markdownItAttrs, {
    allowedAttributes: ['id', 'class', 'style', 'width', 'height', 'align', 'border', /^data-*$/],
  })
  .use(convertAttributesToStylesPlugin)
  .use(addCodeClasses)
  .use(footnotePlugin)
  .use(markdownItMultiMdTable)
}