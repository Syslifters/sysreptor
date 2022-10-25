import { addRemarkExtension } from "./helpers";
import {checkQuote} from 'mdast-util-to-markdown/lib/util/check-quote.js'
import {containerPhrasing} from 'mdast-util-to-markdown/lib/util/container-phrasing.js'
import {track} from 'mdast-util-to-markdown/lib/util/track.js'
import {safe} from 'mdast-util-to-markdown/lib/util/safe.js'
import {all} from 'remark-rehype';
import {normalizeUri} from 'micromark-util-sanitize-uri';


function figureFromMarkdown() {
  // Extend default image formatter from mdast-util-from-markdown to support child markdown text
  return {
    enter: {
      image: enterImage,
    }, 
    exit: {
      label: exitLabel,
    }
  };

  function enterImage(token) {
    this.enter({type: 'image', title: null, url: '', alt: null, children: []}, token);
  }


  /**
   * Label for link or image
   */
  function exitLabel(token) {
    const fragment = /** @type {Fragment} */ (this.stack[this.stack.length - 1]);
    const value = this.resume();
    const node =
      /** @type {(Link|Image) & {identifier: string, label: string}} */ (
        this.stack[this.stack.length - 1]
      );

    // Assume a reference.
    this.setData('inReference', true);

    // @ts-expect-error: Assume static phrasing content.
    node.children = fragment.children;
    if (node.type === 'image') {
      node.alt = value;
    }
  }
}


function figureToMarkdown() {
  image.peek = () => '!';

  return {
    handlers: {
      image
    },
  };

  function image(node, _, context, safeOptions) {
    const quote = checkQuote(context);
    const suffix = quote === '"' ? 'Quote' : 'Apostrophe';
    const exit = context.enter('image');
    let subexit = context.enter('label');
    const tracker = track(safeOptions);
    let value = tracker.move('![');
    value += tracker.move(
      containerPhrasing(node, context, {
        before: value,
        after: '](',
        ...tracker.current()
      })
    );
    value += tracker.move('](');

    subexit();

    if (
      // If there’s no url but there is a title…
      (!node.url && node.title) ||
      // If there are control characters or whitespace.
      /[\0- \u007F]/.test(node.url)
    ) {
      subexit = context.enter('destinationLiteral');
      value += tracker.move('<');
      value += tracker.move(
        safe(context, node.url, {before: value, after: '>', ...tracker.current()})
      );
      value += tracker.move('>');
    } else {
      // No whitespace, raw is prettier.
      subexit = context.enter('destinationRaw');
      value += tracker.move(
        safe(context, node.url, {
          before: value,
          after: node.title ? ' ' : ')',
          ...tracker.current()
        })
      );
    }

    subexit();

    if (node.title) {
      subexit = context.enter('title' + suffix);
      value += tracker.move(' ' + quote);
      value += tracker.move(
        safe(context, node.title, {
          before: value,
          after: quote,
          ...tracker.current()
        })
      );
      value += tracker.move(quote);
      subexit();
    }

    value += tracker.move(')');
    exit();

    return value;
  }
  
}


export function remarkFigure() {
  addRemarkExtension(this, {}, figureFromMarkdown(), figureToMarkdown());
}


export const remarkToRehypeHandlersFigure = {
  image(h, node) {
    // only add attributes to <img> tag, not to <figure>
    const attrs = (node.data || {}).hProperties || {};
    if (!node.data) {
      node.data = {};
    }
    node.data.hProperties = {};

    return h(node, 'figure', [
      h(node, 'img', {src: normalizeUri(node.url), alt: node.alt, ...attrs}),
      ...(node.children.length > 0 ? [h(node, 'figcaption', all(h, node))] : [])
    ]);
  }
};
