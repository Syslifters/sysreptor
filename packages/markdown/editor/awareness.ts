import { EditorView, Decoration, DecorationSet, WidgetType } from "@codemirror/view"


class RemoteSelection extends WidgetType {
  constructor(
    readonly clientID: string,
    readonly name: string,
    readonly color: string,
  ) {
    super()
  }

  toDOM(view: EditorView): HTMLElement {
    const dom = document.createElement
  }
}