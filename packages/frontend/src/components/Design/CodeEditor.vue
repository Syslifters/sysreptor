<template>
  <div ref="editorElement" />
</template>

<script lang="ts">
import * as monaco from 'monaco-editor';
import cssWorkerUrl from 'monaco-editor/esm/vs/language/css/css.worker?worker&url';
import htmlWorkerUrl from 'monaco-editor/esm/vs/language/html/html.worker?worker&url';
import editorWorkerUrl from 'monaco-editor/esm/vs/editor/editor.worker?worker&url';

declare global {
  interface Window {
    MonacoEnvironment: monaco.Environment;
  }
}

self.MonacoEnvironment = {
  getWorkerUrl(_: string, label: string) {
    if (label === 'css') {
      return cssWorkerUrl;
    } else if (label === 'html') {
      return htmlWorkerUrl;
    } else {
      return editorWorkerUrl;
    }
  },
};

monaco.html.htmlLanguageService.defaults.setOptions({
  format: {
    ...monaco.html.htmlLanguageService.defaults.options.format!,
    preserveNewLines: true,
    contentUnformatted: 'markdown,mermaid-diagram,math-latex', // Do not format content of <markdown> tags
    wrapLineLength: 100000000, // Disable max line length
  }
});
monaco.editor.addKeybindingRules([
  {
    keybinding: monaco.KeyMod.CtrlCmd | monaco.KeyCode.Slash,
    command: 'editor.action.commentLine',
  },
  {
    keybinding: monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Digit7,
    command: 'editor.action.commentLine',
  },
])
</script>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: string,
  language?: string,
  readonly?: boolean,
}>(), {
  language: 'plaintext',
  readonly: false,
});
const emits = defineEmits< {
  (e: 'update:modelValue', modelValue: string): void
}>();

const theme = useTheme();

let editor: monaco.editor.IStandaloneCodeEditor;
const editorElement = useTemplateRef('editorElement');

onMounted(() => {
  editor = monaco.editor.create(editorElement.value!, {
    value: props.modelValue,
    language: props.language,
    readOnly: props.readonly,
    theme: theme.current.value.dark ? 'vs-dark' : 'vs',
    minimap: {
      enabled: false,
    },
    contextmenu: false,
    codeLens: false,
    folding: true,
    lightbulb: {
      enabled: monaco.editor.ShowLightbulbIconMode.Off,
    },
    automaticLayout: true,
    wordWrap: 'on',
    fixedOverflowWidgets: true,
  });
  editor.onDidChangeModelContent(() => emits('update:modelValue', editor.getValue()));
});
onBeforeUnmount(() => {
  if (editor) {
    editor.dispose();
  }
})

watch(() => props.modelValue, (val) => {
  if (editor && val !== editor.getValue()) {
    editor.setValue(val);
  }
});
watch(() => props.readonly, (val) => {
  if (editor) {
    editor.updateOptions({ readOnly: val });
  }
});
watch(theme.current, (val) => {
  if (editor) {
    editor.updateOptions({ theme: val.dark ? 'vs-dark' : 'vs' });
  }
});

function jumpToPosition(position: DocumentSelectionPosition) {
  if (!editor) { return; }
  const model = editor.getModel()!;
  const from = model.getPositionAt(position.from)
  const to = model.getPositionAt(position.to);
  editor.setSelection(monaco.Selection.fromPositions(from, to));
  editor.revealPositionInCenter(from);
}

function formatDocument() {
  if (!editor) { return; }
  editor.getAction('editor.action.formatDocument')!.run();
}

defineExpose({
  jumpToPosition,
  formatDocument,
});
</script>
