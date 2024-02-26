import { RangeSetBuilder } from "@codemirror/state";
import { Decoration, type DecorationSet, ViewPlugin, EditorView, ViewUpdate } from "@codemirror/view";

const decorationTodo = Decoration.mark({class: 'tok-todo'});

export const highlightTodos = ViewPlugin.fromClass(class {
  decorations: DecorationSet = Decoration.none;

  constructor(view: EditorView) {
    this.updateDecorations(view);
  }

  update(viewUpdate: ViewUpdate) {
    this.updateDecorations(viewUpdate.view);
  }

  updateDecorations(view: EditorView) {
    const builder = new RangeSetBuilder<Decoration>();
    for (const m of view.state.doc.toString().matchAll(/(TODO|To-Do)/gi)) {
      builder.add(m.index!, m.index! + m[0].length, decorationTodo);
    }
    this.decorations = builder.finish();
  }
}, {decorations: v => v.decorations});
