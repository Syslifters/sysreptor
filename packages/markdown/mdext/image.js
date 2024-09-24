import { normalizeUri } from 'micromark-util-sanitize-uri';
import { addRemarkExtension } from "./helpers";


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
    const fragment = this.stack[this.stack.length - 1];
    const value = this.resume();
    const node = this.stack[this.stack.length - 1];

    // Assume a reference.
    this.data.inReference = true;

    // @ts-expect-error: Assume static phrasing content.
    node.children = fragment.children;
    if (node.type === 'image') {
      node.alt = value;
    }
  }
}


function checkQuote(state) {
  const marker = state.options.quote || '"'

  if (marker !== '"' && marker !== "'") {
    throw new Error(
      'Cannot serialize title with `' +
        marker +
        '` for `options.quote`, expected `"`, or `\'`'
    )
  }

  return marker
}


function figureToMarkdown() {
  image.peek = () => '!';

  return {
    handlers: {
      image
    },
  };

  function image(node, _, state, info) {
    const quote = checkQuote(state);
    const suffix = quote === '"' ? 'Quote' : 'Apostrophe';
    const exit = state.enter('image');
    let subexit = state.enter('label');
    const tracker = state.createTracker(info);
    let value = tracker.move('![');
    value += tracker.move(
      state.containerPhrasing(node, {
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
      subexit = state.enter('destinationLiteral');
      value += tracker.move('<');
      value += tracker.move(
        state.safe(node.url, {before: value, after: '>', ...tracker.current()})
      );
      value += tracker.move('>');
    } else {
      // No whitespace, raw is prettier.
      subexit = state.enter('destinationRaw');
      value += tracker.move(
        state.safe(node.url, {
          before: value,
          after: node.title ? ' ' : ')',
          ...tracker.current()
        })
      );
    }

    subexit();

    if (node.title) {
      subexit = state.enter('title' + suffix);
      value += tracker.move(' ' + quote);
      value += tracker.move(
        state.safe(node.title, {
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
  image(state, node, ...args) {
    // only add attributes to <img> tag, not to <figure>
    const attrs = (node.data || {}).hProperties || {};
    if (node.data) {
      node.data.hProperties = undefined;
    }

    const result = {
      type: 'element',
      tagName: 'figure',
      properties: {
        dataPosition: JSON.stringify(node.position),
      },
      children: [
        {
          type: 'element',
          tagName: 'img',
          properties: {
            src: normalizeUri(node.url),
            alt: node.alt,
            ...attrs,
          },
        },
        ...(node.children.length > 0 ? [{
          type: 'element',
          tagName: 'figcaption',
          children: state.all(node)
        }] : [])
      ],
    };

    state.patch(node, result);
    return state.applyData(node, result);
  }
};
