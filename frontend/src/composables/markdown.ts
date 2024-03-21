import { v4 as uuid4 } from 'uuid';
import type { PropType } from "vue";
import {
  createEditorExtensionToggler,
  EditorState, EditorView, ViewUpdate,
  forceLinting, highlightTodos, tooltips, scrollPastEnd, closeBrackets, 
  drawSelection, rectangularSelection, crosshairCursor, dropCursor,
  history, historyKeymap, keymap, setDiagnostics,
  spellcheck, spellcheckTheme,
  lineNumbers, indentUnit, defaultKeymap, indentWithTab,
  markdown, syntaxHighlighting, markdownHighlightStyle, markdownHighlightCodeBlocks,
  Transaction,
  remoteSelection, setRemoteClients,
} from "reportcreator-markdown/editor/index";
import { MarkdownEditorMode } from '@/utils/types';

export type MarkdownProps = {
  lang?: string|null;
  spellcheckEnabled?: boolean;
  markdownEditorMode?: MarkdownEditorMode;
  collab?: CollabPropType;
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
    readonly: {
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
    spellcheckEnabled: {
      type: Boolean,
      default: undefined,
    },
    markdownEditorMode: {
      type: String as PropType<MarkdownEditorMode>,
      default: MarkdownEditorMode.MARKDOWN_AND_PREVIEW,
    },
    collab: {
      type: Object as PropType<CollabPropType>,
      default: undefined,
    },
    ...(options.files ? {
      uploadFile: {
        type: Function as PropType<MarkdownProps['uploadFile']>,
        default: undefined,
      },
      rewriteFileUrl: {
        type: Function as PropType<MarkdownProps['rewriteFileUrl']>,
        default: undefined,
      },
      rewriteReferenceLink: {
        type: Function as PropType<MarkdownProps['rewriteReferenceLink']>,
        default: undefined,
      },
    } : {}),
  }
}
export function makeMarkdownEmits() {
  return ['update:modelValue', 'update:spellcheckEnabled', 'update:markdownEditorMode', 'collab', 'focus', 'blur'];
}

export function useMarkdownEditor({ props, emit, extensions }: {
    extensions: any[];
    props: ComputedRef<MarkdownProps & {
        modelValue: string|null;
        disabled?: boolean;
        readonly?: boolean;
        spellcheckSupported?: boolean;
    }>;
    emit: any;
}) {
  const apiSettings = useApiSettings();
  const theme = useTheme();
  const editorWasInView = ref(false);

  const valueNotNull = computed(() => props.value.modelValue || '');
  const spellcheckLanguageToolEnabled = computed(() =>
    !props.value.disabled && !props.value.readonly &&
    !!props.value.spellcheckSupported &&
    !!props.value.spellcheckEnabled &&
    editorWasInView.value &&
    apiSettings.spellcheckLanguageToolSupportedForLanguage(props.value.lang));
  const spellcheckBrowserEnabled = computed(() =>
    !props.value.disabled && !props.value.readonly &&
    !!props.value.spellcheckSupported &&
    !!props.value.spellcheckEnabled &&
    !apiSettings.isProfessionalLicense);
  const previewCacheBuster = uuid4();

  async function performSpellcheckRequest(data: any): Promise<any> {
    if (!props.value.lang) {
      return {
        matches: []
      };
    }

    await nextTick();
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
    if (!editorView.value || !props.value.uploadFile || !files || files.length === 0 || fileUploadInProgress.value) {
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
        pos = editorView.value.state.selection.main.to;
      }
      editorView.value.dispatch(editorView.value.state.update({ 
        changes: { from: pos, to: pos, insert: mdFileText },
        selection: { anchor: pos! + mdFileText.length },
      }));
    } finally {
      fileUploadInProgress.value = false;
    }
  }

  function onBeforeApplyRemoteTextChange(event: any) {
    if (editorView.value && event.path === props.value.collab?.path) {
      editorView.value.dispatch(editorView.value.state.update({
        changes: event.changes,
        annotations: [
          Transaction.addToHistory.of(false),
          Transaction.remote.of(true),
        ]
      }));
    }
  }

  const vm = getCurrentInstance()!;
  const editorRef = computed(() => vm.refs.editorRef as HTMLElement);
  const editorView = shallowRef<EditorView|null>(null);
  const editorState = shallowRef<EditorState|null>(null);
  const editorActions = ref<{[key: string]: (enabled: boolean) => void}>({});
  const eventBusBeforeApplyRemoteTextChanges = useEventBus('collab:beforeApplyRemoteTextChanges');
  function initializeEditorView() {
    editorView.value = new EditorView({
      parent: editorRef.value,
      state: EditorState.create({
        doc: valueNotNull.value,
        extensions: [
          ...extensions,
          history(),
          keymap.of([...defaultKeymap, ...historyKeymap]),
          tooltips({ parent: document.body }),
          EditorView.domEventHandlers({
            blur: (event: FocusEvent) => emit('blur', event),
            focus: (event: FocusEvent) => emit('focus', event),
          }),
          EditorView.updateListener.of((viewUpdate: ViewUpdate) => {
            editorState.value = viewUpdate.state;
            // https://discuss.codemirror.net/t/codemirror-6-proper-way-to-listen-for-changes/2395/11
            if (viewUpdate.docChanged && viewUpdate.state.doc.toString() !== valueNotNull.value) {
              // Collab updates
              if (props.value.collab) {
                for (const tr of viewUpdate.transactions) {
                  if (tr.docChanged && !tr.annotation(Transaction.remote)) {
                    emit('collab', {
                      type: 'collab.update_text',
                      path: props.value.collab.path,
                      updates: [{ changes: tr.changes, selection: tr.selection }],
                    });
                  }
                }
              }

              // Model-value updates
              emit('update:modelValue', viewUpdate.state.doc.toString());
            } 
            
            if (props.value.collab && (viewUpdate.selectionSet || viewUpdate.focusChanged)) {
              // Collab awareness updates
              const hasFocus = editorView.value?.hasFocus || false;
              emit('collab', {
                type: 'collab.awareness',
                path: props.value.collab.path,
                focus: hasFocus,
                selection: viewUpdate.state.selection,
              });
            }
          }),
          remoteSelection(),
        ]
      }),
    });
    eventBusBeforeApplyRemoteTextChanges.on(onBeforeApplyRemoteTextChange);

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
      darkTheme: createEditorExtensionToggler(editorView.value, [
        EditorView.theme({}, { dark: true }),
      ]),
    };
    editorActions.value.disabled(Boolean(props.value.disabled || props.value.readonly));
    editorActions.value.spellcheckLanguageTool(spellcheckLanguageToolEnabled.value);
    editorActions.value.spellcheckBrowser(spellcheckBrowserEnabled.value);
    editorActions.value.uploadFile(Boolean(props.value.uploadFile));
    editorActions.value.darkTheme(theme.current.value.dark);
  }
  onMounted(() => initializeEditorView());
  onBeforeUnmount(() => {
    eventBusBeforeApplyRemoteTextChanges.off(onBeforeApplyRemoteTextChange);
    if (editorView.value) {
      editorView.value.destroy();
    }
  });
  function onIntersect(isIntersecting: boolean) {
    if (isIntersecting) {
      editorWasInView.value = true;
    }
  }

  watch(valueNotNull, () => {
    if (editorView.value && valueNotNull.value !== editorView.value.state.doc.toString()) {
      editorView.value.dispatch(editorView.value.state.update({
        changes: {
          from: 0,
          to: editorView.value.state.doc.length,
          insert: valueNotNull.value,
        },
      }));
    }
  });
  watch([() => props.value.disabled, () => props.value.readonly], () => editorActions.value.disabled?.(Boolean(props.value.disabled || props.value.readonly)));
  watch(() => props.value.lang, () => {
    if (spellcheckLanguageToolEnabled.value && editorView.value) {
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
  watch(theme.current, val => editorActions.value.darkTheme?.(val.dark));

  watch([() => props.value.collab?.clients, () => editorView.value], () => {
    if (!editorView.value) {
      return;
    }
    const remoteClients = (props.value.collab?.clients || []).filter(c => !c.isSelf && c.selection).map(c => ({
      client_id: c.client_id,
      color: c.client_color,
      name: c.user.username + (c.user.name ? ` (${c.user.name})` : ''),
      selection: c.selection!,
    }));
    if (remoteClients.length > 0) {
      console.log('markdown collab.clients', remoteClients.map(a => ({ ...a, selection: a.selection?.toJSON() })));
    }

    editorView.value.dispatch({
      effects: [
        setRemoteClients.of(remoteClients)
      ]
    })
  }, { deep: true });

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
    disabled: props.value.disabled || props.value.readonly,
    uploadFiles: props.value.uploadFile ? uploadFiles : undefined,
    fileUploadInProgress: fileUploadInProgress.value,
    lang: props.value.lang,
    spellcheckEnabled: props.value.spellcheckEnabled,
    'onUpdate:spellcheckEnabled': (val: boolean) => emit('update:spellcheckEnabled', val),
    markdownEditorMode: props.value.markdownEditorMode,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => emit('update:markdownEditorMode', val),
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
    cacheBuster: previewCacheBuster,
  }));

  return {
    editorView,
    editorState,
    editorActions,
    markdownToolbarAttrs,
    markdownStatusbarAttrs,
    markdownPreviewAttrs,
    onIntersect,
    focus,
    blur,
  }
}

export function markdownEditorDefaultExtensions() {
  return [
    lineNumbers(),
    EditorState.allowMultipleSelections.of(true),
    drawSelection(),
    rectangularSelection(),
    crosshairCursor(),
    dropCursor(),
    EditorView.lineWrapping,
    EditorState.tabSize.of(4),
    indentUnit.of('    '),
    keymap.of([indentWithTab]),
    closeBrackets(),
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
