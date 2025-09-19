<template>
  <div class="editor-field-wrapper">
    <div ref="editorRef" class="editor-field" />
  </div>
</template>

<script setup lang="ts">
import { 
  EditorState, 
  EditorView, 
  keymap, 
  history, 
  historyKeymap, 
  defaultKeymap, 
  tooltips,
  autocompletion, 
  type CompletionContext,
} from '@sysreptor/markdown/editor';

const modelValue = defineModel<string>({ required: true });
const props = defineProps<{
  selectableUsers?: UserShortInfo[];
}>();
const emit = defineEmits<{
  'focus': [];
  'save': [];
}>();

const editorRef = useTemplateRef('editorRef');
const editorView = ref<EditorView|null>(null);

onMounted(() => {
  editorView.value = new EditorView({
    parent: editorRef.value!,
    state: EditorState.create({
      doc: modelValue.value,
      extensions: [
        history(),
        keymap.of([
          { key: 'Ctrl-Enter', preventDefault: true, run: () => { emit('save'); return true; }},
          ...defaultKeymap,
          ...historyKeymap,
        ]),
        tooltips({ parent: document.body }),
        autocompletion({
          override: [autocompleteUsernames],
          icons: false,
        }),
        EditorView.lineWrapping,
        EditorView.theme({
          '.cm-tooltip-autocomplete': {
            zIndex: 2000,
            backgroundColor: 'rgba(var(--v-theme-surface), 1)',
            borderRadius: '4px',
            '& > ul': {
              fontFamily: 'inherit !important',
            },
            '& > ul > li[aria-selected]': {
              background: 'rgba(var(--v-theme-on-surface), calc(var(--v-activated-opacity) * var(--v-theme-overlay-multiplier)))',
              color: 'inherit',
            },
          },
        }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            modelValue.value = update.state.doc.toString();
          }
        }),
      ],
    }),
  });
});

watch(modelValue, () => {
  if (editorView.value && editorView.value.state.doc.toString() !== modelValue.value) {
    editorView.value.dispatch({
      changes: { from: 0, to: editorView.value.state.doc.length ?? 0, insert: modelValue.value }
    });
  }
})


function autocompleteUsernames(context: CompletionContext) {
  if (!props.selectableUsers || props.selectableUsers.length === 0) {
    return null;
  }

  const word = context.matchBefore(/@\w*/);
  if (!word && !context.explicit) {
    return null;
  }
  const from = word ? word.from : context.pos;
  return {
    from,
    options: props.selectableUsers
      .filter(u => !!u.username)
      .map(u => ({ label: `@${u.username}`, detail: u.name || undefined })),
  };
}


function focus() {
  if (editorView.value) {
    editorView.value.focus();
    emit('focus');
  }
}
function blur() {
  if (editorView.value) {
    editorView.value.dom.blur();
  }
}

defineExpose({
  focus,
  blur,
});
</script>

<style lang="scss" scoped>
@use "@base/assets/vuetify.scss" as vuetify;
@use "@base/assets/settings" as settings;

.editor-field, .editor-field-wrapper {
  width: 100%;
  max-width: 100%;
  display: inline-block;
  font-size: vuetify.$card-text-font-size;
}

:deep(.editor-field) {
  .cm-focused {
    outline: none !important;
  }
  .cm-content {
    font-family: settings.$body-font-family;
    padding: 0;
  }
  .cm-line {
    padding-left: 0;
  }

  .cm-scroller {
    // Hide scrollbar
    overflow: hidden;
    // Prevent cutting off spellcheck error underline
    padding-bottom: 1px;
  }
}
</style>
