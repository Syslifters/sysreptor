import { Compartment, StateEffect } from '@codemirror/state';

export function createEditorCompartment(view) {
  const compartment = new Compartment();
  const run = (extension) => {
    compartment.get(view.state)
      ? view.dispatch({ effects: compartment.reconfigure(extension) }) // reconfigure
      : view.dispatch({ effects: StateEffect.appendConfig.of(compartment.of(extension)) }) // inject
  }
  return { compartment, run }
}

export function createEditorExtensionToggler(view, extension) {
  const { compartment, run } = createEditorCompartment(view)
  return (targetApply) => {
    const exExtension = compartment.get(view.state)
    const apply = targetApply ?? exExtension !== extension
    run(apply ? extension : [])
  }
}
