import { Compartment, type Extension, StateEffect } from '@codemirror/state';
import { EditorView } from '@codemirror/view';

export function createEditorCompartment(view: EditorView) {
  const compartment = new Compartment();
  const run = (extension: Extension) => {
    compartment.get(view.state)
      ? view.dispatch({ effects: compartment.reconfigure(extension) }) // reconfigure
      : view.dispatch({ effects: StateEffect.appendConfig.of(compartment.of(extension)) }) // inject
  }
  return { compartment, run }
}

export function createEditorExtensionToggler(view: EditorView, extension: Extension) {
  const { compartment, run } = createEditorCompartment(view)
  return (targetApply: boolean) => {
    const exExtension = compartment.get(view.state)
    const apply = targetApply ?? exExtension !== extension
    run(apply ? extension : [])
  }
}
