<template>
  <div ref="editorElement" />
</template>

<script lang="ts">
import * as monaco from 'monaco-editor';

// @ts-ignore
self.MonacoEnvironment = {
  async getWorker(_: any, label: string) {
    let worker;
    if (label === 'css') {
      worker = await import('monaco-editor/esm/vs/language/css/css.worker?worker');
    } else if (label === 'html') {
      worker = await import('monaco-editor/esm/vs/language/html/html.worker?worker');
    } else {
      worker = await import('monaco-editor/esm/vs/editor/editor.worker?worker');
    }
    // eslint-disable-next-line new-cap
    return new worker.default();
  }
};

monaco.languages.html.htmlDefaults.setOptions({
  format: {
    preserveNewLines: true,
    contentUnformatted: 'markdown,mermaid-diagram', // Do not format content of <markdown> tags
    wrapLineLength: 100000000, // Disable max line length
  } as any
});
</script>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: string,
  language?: string,
  disabled?: boolean,
}>(), {
  language: 'plaintext',
  disabled: false,
});
const emits = defineEmits< {
  (e: 'update:modelValue', modelValue: string): void
}>();

const theme = useTheme();

let editor: monaco.editor.IStandaloneCodeEditor;
const editorElement = ref<HTMLElement>();

onMounted(() => {
  editor = monaco.editor.create(editorElement.value!, {
    value: props.modelValue,
    language: props.language,
    readOnly: props.disabled,
    theme: theme.current.value.dark ? 'vs-dark' : 'vs',
    minimap: {
      enabled: false,
    },
    contextmenu: false,
    codeLens: false,
    folding: true,
    lightbulb: {
      enabled: false,
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
watch(() => props.disabled, (val) => {
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
