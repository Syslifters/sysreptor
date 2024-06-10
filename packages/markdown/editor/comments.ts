import { EditorSelection, RangeSet, RangeValue, SelectionRange, StateEffect, StateField } from "@codemirror/state"
import { Decoration, type DecorationSet, EditorView, hoverTooltip, layer, RectangleMarker, type Tooltip } from "@codemirror/view"

export type CommentInfo = {
  id: string;
  text_position: SelectionRange;
};
export const setComments = StateEffect.define<CommentInfo[]>();

const commentField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(comments, tr) {
    const newComments = tr.effects.find(e => e.is(setComments))?.value as CommentInfo[]|undefined;
    if (newComments) {
      return comments.update({
        filter: () => false,
        add: newComments.map(c => Decoration.mark({
          class: 'cm-comment',
          attributes: { id: `comment-textrange-${c.id}` },
        }).range(c.text_position.from, c.text_position.to)),
      })
    } else {
      return comments.map(tr.changes).update({
        filter: (from, to) => from !== to,
      });
    }
  },
  provide: f => EditorView.decorations.from(f),
});


const commentTheme = EditorView.theme({
  '.cm-comment': {
    // TODO: comment color (needs transparency)
    backgroundColor: 'rgba(255, 255, 0, 0.4)',
    cursor: 'pointer',
  },
});

export function commentsExtension() {
  return [
    commentField,
    commentTheme,
  ];
}