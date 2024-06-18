// @ts-ignore
import { sortBy } from 'lodash-es';
import { SelectionRange, StateEffect, StateField } from "@codemirror/state"
import { Decoration, type DecorationSet, EditorView } from "@codemirror/view"


export type CommentInfo = {
  id: string;
  text_range: SelectionRange;
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
        add: sortBy(newComments, ['text_range.from']).map((c: CommentInfo) => Decoration.mark({
          class: 'cm-comment',
          attributes: { id: `comment-textrange-${c.id}` },
        }).range(c.text_range.from, c.text_range.to)),
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
    backgroundColor: 'rgba(255, 193, 7, 0.4)',
    cursor: 'pointer',
  },
});

export function commentsExtension() {
  return [
    commentField,
    commentTheme,
  ];
}