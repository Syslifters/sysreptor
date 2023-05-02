import { RangeSetBuilder } from "@codemirror/state";
import { Decoration, ViewPlugin } from "@codemirror/view";

const decorationTodo = Decoration.mark({class: 'tok-todo'});

export const highlightTodos = ViewPlugin.fromClass(class {
  decorations = Decoration.none;

  constructor(view) {
    this.updateDecorations(view);
  }

  update(viewUpdate) {
    this.updateDecorations(viewUpdate.view);
  }

  updateDecorations(view) {
    const builder = new RangeSetBuilder();
    for (const m of view.state.doc.toString().matchAll(/(TODO|To-Do)/gi)) {
      builder.add(m.index, m.index + m[0].length, decorationTodo);
    }
    this.decorations = builder.finish();
  }
}, {decorations: v => v.decorations});
