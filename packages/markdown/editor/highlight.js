import { syntaxTree } from "@codemirror/language";
import { RangeSetBuilder } from "@codemirror/state";
import { Decoration, ViewPlugin } from "@codemirror/view";
import { tags as t, Tag, tagHighlighter } from "@lezer/highlight";
import { linesInRange } from "./codemirror-utils";

export const tags = {
  codeblock: Tag.define(),
  inlinecode: Tag.define(),
  footnote: Tag.define(),
  table: Tag.define(),
  todo: Tag.define(),
};

      
export const markdownHighlightStyle = tagHighlighter([
  {tag: t.heading1, class: 'tok-h1'},
  {tag: t.heading2, class: 'tok-h2'},
  {tag: t.heading3, class: 'tok-h3'},
  {tag: t.heading4, class: 'tok-h4'},
  {tag: t.heading5, class: 'tok-h5'},
  {tag: t.heading6, class: 'tok-h6'},
  {tag: t.strong, class: 'tok-strong'},
  {tag: t.emphasis, class: 'tok-emphasis'},
  {tag: t.strikethrough, class: 'tok-strikethrough'},
  {tag: t.link, class: 'tok-link'},
  {tag: t.url, class: 'tok-url'},
  {tag: t.quote, class: 'tok-quote'},

  {tag: tags.inlinecode, class: 'tok-inlinecode'},
  {tag: tags.table, class: 'tok-table'},
  {tag: tags.footnote, class: 'tok-footnote'},
  {tag: tags.todo, class: 'tok-todo'},

  {tag: t.tagName, class: 'tok-tagname'},
  {tag: t.angleBracket, class: 'tok-anglebracket'},
  {tag: t.attributeName, class: 'tok-attributename'},
  {tag: t.attributeValue, class: 'tok-attributevalue'},
  {tag: t.comment, class: 'tok-comment'},
]);


// https://discuss.codemirror.net/t/how-to-define-highlighting-styles-for-blocks/4029
export const markdownHighlightCodeBlocks = ViewPlugin.fromClass(class {
  decorations = Decoration.none;

  constructor(view) {
    this.updateDecorations(view);
  }

  update(update) {
    this.updateDecorations(update.view);
  }

  updateDecorations(view) {
    let builder = new RangeSetBuilder();
    syntaxTree(view.state).iterate({
      enter: (n) => {
        if (n.name === 'codeFenced') {
          for (const l of linesInRange(view.state.doc, n)) {
            builder.add(l.from, l.from, Decoration.line({class: 'tok-codeblock'}));
          }    
        }
      }
    })
    this.decorations = builder.finish();
  }
}, {decorations: v => v.decorations});