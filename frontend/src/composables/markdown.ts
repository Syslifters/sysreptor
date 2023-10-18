import {
  createEditorExtensionToggler,
  EditorState, EditorView, ViewUpdate,
  forceLinting, highlightTodos, tooltips, scrollPastEnd,
  history, historyKeymap, keymap, setDiagnostics,
  spellcheck, spellcheckTheme,
  lineNumbers, indentUnit, defaultKeymap, indentWithTab, markdown,
  syntaxHighlighting, markdownHighlightStyle, markdownHighlightCodeBlocks
  // @ts-ignore
} from "reportcreator-markdown/editor";

export type MarkdownProps = {
  lang?: string|null;
  uploadFile?: (file: File) => Promise<string>;
  rewriteFileUrl?: (fileSrc: string) => string;
  rewriteReferenceLink?: (src: string) => {href: string, title: string}|null;
}

export function makeMarkdownProps(options: { files: boolean, spellcheckSupportedDefault: boolean }) {
  return {
    modelValue: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    lang: {
      type: String,
      default: null,
    },
    spellcheckSupported: {
      type: Boolean,
      default: options.spellcheckSupportedDefault,
    },
    ...(options.files ? {
      uploadFile: {
        type: Function,
        default: undefined,
      },
      rewriteFileUrl: {
        type: Function,
        default: undefined,
      },
      rewriteReferenceLink: {
        type: Function,
        default: undefined,
      },
    } : {}),
  }
}
export function makeMarkdownEmits() {
  return ['update:modelValue', 'focus', 'blur'];
}

export function useMarkdownEditor({ props, emit, extensions }: {
    extensions: any[];
    props: ComputedRef<{
        modelValue: string|null;
        disabled?: boolean;
        lang?: string|null;
        spellcheckSupported?: boolean;
        uploadFile?: (file: File) => Promise<string>;
        rewriteFileUrl?: (fileSrc: string) => string;
        rewriteReferenceLink?: (src: string) => string|null;
    }>;
    emit: any;
}) {
  const localSettings = useLocalSettings();

  const valueNotNull = computed(() => props.value.modelValue || '');
  const spellcheckLanguageToolEnabled = computed(() =>
    !props.value.disabled &&
    !!props.value.spellcheckSupported &&
    localSettings.spellcheckLanguageToolEnabled(props.value.lang || null))
  const spellcheckBrowserEnabled = computed(() =>
    !props.value.disabled &&
    !!props.value.spellcheckSupported &&
    localSettings.spellcheckBrowserEnabled(props.value.lang || null))

  async function performSpellcheckRequest(data: any): Promise<any> {
    if (!props.value.lang) {
      return {
        matches: []
      };
    }

    return await $fetch('/api/v1/utils/spellcheck/', {
      method: 'POST',
      body: {
        ...data,
        language: props.value.lang
      }
    });
  }
  async function performSpellcheckAddWordRequest(data: any): Promise<void> {
    try {
      await $fetch('/api/v1/utils/spellcheck/words/', {
        method: 'POST',
        body: data
      });
    } catch (error) {
      requestErrorToast({ error });
    }
  }

  const fileUploadInProgress = ref(false);
  async function uploadFiles(files?: FileList, pos?: number|null) {
    if (!props.value.uploadFile || !files || files.length === 0 || fileUploadInProgress.value) {
      return;
    }

    try {
      fileUploadInProgress.value = true;
      const results = await Promise.all(Array.from(files).map(async (file: File) => {
        try {
          return await props.value.uploadFile!(file);
        } catch (error) {
          requestErrorToast({ error, message: 'Failed to upload ' + file.name })
          return null;
        }
      }));

      const mdFileText = results.filter(u => u).join('\n');
      if (pos === undefined || pos === null) {
        pos = editorView.value.state.selection.main.from;
      }
      editorView.value.dispatch({ changes: { from: pos, to: pos, insert: mdFileText } });
    } finally {
      fileUploadInProgress.value = false;
    }
  }

  const vm = getCurrentInstance()!;
  const editorRef = computed(() => vm.refs.editorRef);
  const editorView = shallowRef<EditorView|null>(null);
  const editorState = shallowRef<EditorState|null>(null);
  const editorActions = ref<{[key: string]: (enabled: boolean) => void}>({});
  function initializeEditorView() {
    editorView.value = new EditorView({
      parent: editorRef.value,
      state: EditorState.create({
        doc: valueNotNull.value,
        extensions: [
          ...extensions,
          history(),
          keymap.of([historyKeymap]),
          tooltips({ parent: document.body }),
          EditorView.domEventHandlers({
            blur: (event: FocusEvent) => emit('blur', event),
            focus: (event: FocusEvent) => emit('focus', event),
          }),
          EditorView.updateListener.of((viewUpdate: ViewUpdate) => {
            editorState.value = viewUpdate.state;
            // https://discuss.codemirror.net/t/codemirror-6-proper-way-to-listen-for-changes/2395/11
            if (viewUpdate.docChanged && viewUpdate.state.doc.toString() !== valueNotNull.value) {
              emit('update:modelValue', viewUpdate.state.doc.toString());
            }
          }),
        ]
      }),
    });
    editorState.value = editorView.value.state;
    editorActions.value = {
      disabled: createEditorExtensionToggler(editorView.value, [
        EditorView.editable.of(false),
        EditorState.readOnly.of(true),
      ]),
      spellcheckLanguageTool: createEditorExtensionToggler(editorView.value, [
        spellcheck({
          performSpellcheckRequest,
          performSpellcheckAddWordRequest,
        }),
        spellcheckTheme,
      ]),
      spellcheckBrowser: createEditorExtensionToggler(editorView.value, [
        EditorView.contentAttributes.of({ spellcheck: "true" }),
      ]),
      uploadFile: createEditorExtensionToggler(editorView.value, [
        EditorView.domEventHandlers({
          drop: (event: DragEvent) => {
            event.stopPropagation();
            event.preventDefault();
            const dropPos = editorView.value!.posAtCoords({ x: event.clientX, y: event.clientY });
            uploadFiles(event.dataTransfer?.files, dropPos);
          },
          paste: (event: ClipboardEvent) => {
            if ((event.clipboardData?.files?.length || 0) > 0) {
              event.stopPropagation();
              event.preventDefault();
              uploadFiles(event.clipboardData!.files);
            }
          }
        })
      ]),
    };
    editorActions.value.disabled(Boolean(props.value.disabled));
    editorActions.value.spellcheckLanguageTool(spellcheckLanguageToolEnabled.value);
    editorActions.value.spellcheckBrowser(spellcheckBrowserEnabled.value);
    editorActions.value.uploadFile(Boolean(props.value.uploadFile));
  }
  onMounted(() => initializeEditorView());
  onBeforeUnmount(() => {
    if (editorView.value) {
      editorView.value.destroy();
    }
  });

  watch(valueNotNull, () => {
    if (editorView.value && valueNotNull.value !== editorView.value.state.doc.toString()) {
      editorView.value.dispatch({
        changes: {
          from: 0,
          to: editorView.value.state.doc.length,
          insert: valueNotNull.value,
        }
      });
    }
  });
  watch(() => props.value.disabled, () => editorActions.value.disabled?.(Boolean(props.value.disabled)));
  watch(() => props.value.lang, () => {
    if (spellcheckLanguageToolEnabled.value) {
      forceLinting(editorView.value);
    }
  });
  watch(spellcheckLanguageToolEnabled, (val) => {
    editorActions.value?.spellcheckLanguageTool(val);
    if (!val && editorView.value) {
    // clear existing spellcheck items from editor
      editorView.value.dispatch(setDiagnostics(editorView.value.state, []));
    }
  });
  watch(spellcheckBrowserEnabled, val => editorActions.value.spellcheckBrowser?.(val));

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

  const markdownToolbarAttrs = computed(() => ({
    editorView: editorView.value,
    editorState: editorState.value,
    disabled: props.value.disabled,
    uploadFiles: props.value.uploadFile ? uploadFiles : undefined,
    fileUploadInProgress: fileUploadInProgress.value,
    lang: props.value.lang,
  }));
  const markdownStatusbarAttrs = computed(() => ({
    editorState: editorState.value,
    fileUploadEnabled: Boolean(props.value.uploadFile),
    fileUploadInProgress: fileUploadInProgress.value,
  }));
  const markdownPreviewAttrs = computed(() => ({
    value: props.value.modelValue,
    rewriteFileUrl: props.value.rewriteFileUrl,
    rewriteReferenceLink: props.value.rewriteReferenceLink,
  }));

  return {
    editorView,
    editorState,
    editorActions,
    markdownToolbarAttrs,
    markdownStatusbarAttrs,
    markdownPreviewAttrs,
    focus,
    blur,
  }
}

export function markdownEditorDefaultExtensions() {
  return [
    lineNumbers(),
    EditorState.allowMultipleSelections.of(true),
    EditorView.lineWrapping,
    EditorState.tabSize.of(4),
    indentUnit.of('    '),
    keymap.of([defaultKeymap, indentWithTab, historyKeymap]),
    markdown(),
    syntaxHighlighting(markdownHighlightStyle),
    markdownHighlightCodeBlocks,
  ];
}

export function markdownEditorTextFieldExtensions() {
  return [
    highlightTodos,
    // Prevent newlines
    EditorState.transactionFilter.of((tr: any) => {
      const changesWithoutNewlines = [] as any[];
      let transactionModified = false;
      tr.changes.iterChanges((from: number, to: number, _fromB: number, _toB: number, insert: any) => {
        if (insert.text.length > 1) {
          insert = insert.text.join('');
          transactionModified = true;
        }
        changesWithoutNewlines.push({ from, to, insert })
      });

      return transactionModified ? {
        annotations: tr.annotations,
        effects: tr.effects,
        scrollIntoView: tr.scrollIntoView,
        changes: changesWithoutNewlines,
      } : tr;
    }),
  ]
}

export function markdownEditorPageExtensions() {
  return [
    ...markdownEditorDefaultExtensions(),
    scrollPastEnd(),
  ]
}
