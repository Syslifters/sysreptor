import {splice} from 'micromark-util-chunked'
import {codes} from 'micromark-util-symbol/codes.js'
import {resolveAll} from 'micromark-util-resolve-all'
import {containerPhrasing} from 'mdast-util-to-markdown/lib/util/container-phrasing.js'
import {all} from 'remark-rehype';
import {visit} from 'unist-util-visit';
import { addRemarkExtension, assert } from './helpers';
import {h} from 'hastscript';

/**
 * @typedef {import('micromark-util-types').Extension} Extension
 * @typedef {import('micromark-util-types').Resolver} Resolver
 * @typedef {import('micromark-util-types').Token} Token
 * @typedef {import('micromark-util-types').Tokenizer} Tokenizer
 * @typedef {import('micromark-util-types').Exiter} Exiter
 * @typedef {import('micromark-util-types').State} State
 * @typedef {import('micromark-util-types').HtmlExtension} HtmlExtension
 * @typedef {import('micromark-util-types').CompileContext} CompileContext
 * 
 * @typedef {import('mdast-util-from-markdown').Extension} FromMarkdownExtension
 * @typedef {import('mdast-util-from-markdown').Handle} FromMarkdownHandle
 * @typedef {import('mdast-util-to-markdown').Options} ToMarkdownExtension
 * @typedef {import('mdast-util-to-markdown').Handle} ToMarkdownHandle
 * @typedef {import('mdast-util-to-markdown').Map} Map
 */
 

/**
 * @returns {Extension}
 */
function footnoteSyntax() {
  /** @type {Extension} */
  return {
    _hiddenFootnoteSupport: {},
    text: {
      [codes.caret]: {
        tokenize: tokenizeInlineFootnoteStart, 
        resolveAll: resolveAllFootnote
      },
      [codes.rightSquareBracket]: {
        add: 'after',
        tokenize: tokenizeInlineFootnoteEnd,
        resolveAll: resolveAllFootnote,
        resolveTo: resolveToFootnoteEnd
      },  
    }
  };

  /** @type {Tokenizer} */
  function tokenizeInlineFootnoteStart(effects, ok, nok) {
    return start;

    /** @type {State} */
    function start(code) {
      assert(code === codes.caret, 'expected `^`');
      effects.enter('inlineFootnoteStart');
      effects.enter('inlineFootnoteMarker');
      effects.consume(code);
      effects.exit('inlineFootnoteMarker');
      return inlineFootnoteStart;
    }

    /** @type {State} */
    function inlineFootnoteStart(code) {
      if (code !== codes.leftSquareBracket) {
        return nok(code);
      }

      effects.enter('inlineFootnoteStartMarker');
      effects.consume(code);
      effects.exit('inlineFootnoteStartMarker');
      effects.exit('inlineFootnoteStart');
      return ok;
    }
  }

  /** @type {Tokenizer} */
  function tokenizeInlineFootnoteEnd(effects, ok, nok) {
    const self = this;
    return start;

    /** @type {State} */
    function start(code) {
      assert(code === codes.rightSquareBracket, 'expected `]`');
      let index = self.events.length;
      /** @type {boolean|undefined} */
      let hasStart;

      // Find an opening.
      while (index--) {
        if (self.events[index][1].type === 'inlineFootnoteStart') {
          hasStart = true;
          break;
        }
      }

      if (!hasStart) {
        return nok(code);
      }

      effects.enter('inlineFootnoteEnd');
      effects.enter('inlineFootnoteEndMarker');
      effects.consume(code);
      effects.exit('inlineFootnoteEndMarker');
      effects.exit('inlineFootnoteEnd');
      return ok;
    }
  }

  /**
   * Remove remaining note starts.
   *
   * @type {Resolver}
   */
  function resolveAllFootnote(events) {
    let index = -1;
    /** @type {Token} */
    let token;

    while (++index < events.length) {
      token = events[index][1];

      if (events[index][0] === 'enter' && token.type === 'inlineFootnoteStart') {
        token.type = 'data';
        // Remove the two marker (`^[`).
        events.splice(index + 1, 4);
      }
    }

    return events;
  }

  /** @type {Resolver} */
  function resolveToFootnoteEnd(events, context) {
    let index = events.length - 4;
    /** @type {Token} */
    let token;
    /** @type {number} */
    let openIndex;

    // Find an opening.
    while (index--) {
      token = events[index][1];

      // Find where the note starts.
      if (events[index][0] === 'enter' && token.type === 'inlineFootnoteStart') {
        openIndex = index;
        break;
      }
    }

    // @ts-expect-error It’s fine.
    assert(openIndex !== undefined, 'expected `openIndex` to be found');

    /** @type {Token} */
    const group = {
      type: 'inlineFootnote',
      start: Object.assign({}, events[openIndex][1].start),
      end: Object.assign({}, events[events.length - 1][1].end),
    }

    const text = {
      type: 'inlineFootnoteText',
      start: Object.assign({}, events[openIndex + 4][1].end),
      end: Object.assign({}, events[events.length - 3][1].start),
    }

    const note = [
      ['enter', group, context],
      events[openIndex + 1],
      events[openIndex + 2],
      events[openIndex + 3],
      events[openIndex + 4],
      ['enter', text, context]
    ];

    splice(
      note,
      note.length,
      0,
      resolveAll(
        context.parser.constructs.insideSpan.null,
        events.slice(openIndex + 6, -4),
        context
      )
    );

    note.push(
      ['exit', text, context],
      events[events.length - 3],
      events[events.length - 2],
      ['exit', group, context]
    );

    splice(events, index, events.length - index, note);

    return events;
  }
}



function footnoteFromMarkdown() {
  /** @type {FromMarkdownExtension} */
  return {
    enter: {
      inlineFootnote: enterInlineFootnote,
    },
    exit: {
      inlineFootnote: exitInlineFootnote,
    }
  };

  function enterInlineFootnote(token) {
    this.enter({type: 'footnote', children: []}, token);
  }

  function exitInlineFootnote(token) {
    this.exit(token);
  }
}

function footnoteToMarkdown() {
  return {
    unsafe: [{character: '[', inConstruct: ['phrasing', 'label', 'reference']}],
    handlers: {footnote},
  };

  function footnote(node, _, context) {
    const exit = context.enter('footnote');
    const subexit = context.enter('label');
    const value = '^[' + containerPhrasing(node, context, {before: '[', after: ']'}) + ']';
    subexit();
    exit();
    return value;
  }
};



export function remarkFootnotes() {
  addRemarkExtension(this, footnoteSyntax(), footnoteFromMarkdown(), footnoteToMarkdown());
}


/**
 * Render footnotes as <footnote>content</footnote>
 */
export const remarkToRehypeHandlersFootnotes = {
  footnote(h, node) {
    return h(node, 'footnote', all(h, node))
  },
  footnoteDefinition(h, node) {
    return null;
  },
  footnoteReference(h, node) {
    return null;
  },
};


export function rehypeFootnoteSeparator() {
  // add a footnote call separator tag between consecutive <footnote> tags
  return tree => visit(tree, 'element', (node, index, parent) => {
    if (node.tagName === 'footnote' && parent.children[index + 1]?.tagName === 'footnote') {
      parent.children.splice(index + 1, 0, h('sup', {class: 'footnote-call-separator'}));
    }
  })
}


export function rehypeFootnoteSeparatorPreview() {
  return tree => visit(tree, 'element', (node, index, parent) => {
    // Remove link from footnote call
    if (node.tagName !== 'sup' || node.children.length !== 1 || !node.children[0]?.properties?.dataFootnoteRef) {
      return;
    }
    node.children = node.children[0].children;

    // Add footnote call separator
    const nextSibling = parent.children[index + 1];
    if (nextSibling?.tagName !== 'sup' || nextSibling.children.length !== 1 || !nextSibling.children[0]?.properties?.dataFootnoteRef) {
      return;
    }
    parent.children.splice(index + 1, 0, h('sup', {class: 'footnote-call-separator'}, [',']));
  })
}