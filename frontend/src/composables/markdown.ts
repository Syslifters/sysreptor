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
  type Extension,
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

export function makeMarkdownProps(options: { spellcheckSupportedDefault: boolean } = { spellcheckSupportedDefault: true }) {
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
  }
}
export function makeMarkdownEmits() {
  return ['update:modelValue', 'update:spellcheckEnabled', 'update:markdownEditorMode', 'collab', 'focus', 'blur'];
}

export function useMarkdownEditorBase(options: {
  editorView: Ref<EditorView|null>;
  extensions: Extension[];
  props: ComputedRef<MarkdownProps & {
    modelValue: string|null;
    disabled?: boolean;
    readonly?: boolean;
    spellcheckSupported?: boolean;
  }>;
  emit: any;
  fileUploadSupported: boolean;
}) {
  const apiSettings = useApiSettings();
  const theme = useTheme();
  const editorWasInView = ref(false);
  const previewCacheBuster = uuid4();

  const valueNotNull = computed(() => options.props.value.modelValue || '');
  const spellcheckLanguageToolEnabled = computed(() =>
    !options.props.value.disabled && !options.props.value.readonly &&
    !!options.props.value.spellcheckSupported &&
    !!options.props.value.spellcheckEnabled &&
    editorWasInView.value &&
    apiSettings.spellcheckLanguageToolSupportedForLanguage(options.props.value.lang));
  const spellcheckBrowserEnabled = computed(() =>
    !options.props.value.disabled && !options.props.value.readonly &&
    !!options.props.value.spellcheckSupported &&
    !!options.props.value.spellcheckEnabled &&
    !apiSettings.isProfessionalLicense);
  const fileUploadEnabled = computed(() => options.fileUploadSupported && Boolean(options.props.value.uploadFile));

  async function performSpellcheckRequest(data: any): Promise<any> {
    if (!options.props.value.lang) {
      return {
        matches: []
      };
    }
  
    await nextTick();
    return await $fetch('/api/v1/utils/spellcheck/', {
      method: 'POST',
      body: {
        ...data,
        language: options.props.value.lang
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
    if (!options.editorView.value || !fileUploadEnabled.value || !files || files.length === 0 || fileUploadInProgress.value) {
      return;
    }
  
    try {
      fileUploadInProgress.value = true;
      const results = await Promise.all(Array.from(files).map(async (file: File) => {
        try {
          return await options.props.value.uploadFile!(file);
        } catch (error) {
          requestErrorToast({ error, message: 'Failed to upload ' + file.name })
          return null;
        }
      }));
  
      const mdFileText = results.filter(u => u).join('\n');
      if (pos === undefined || pos === null) {
        pos = options.editorView.value.state.selection.main.to;
      }
      options.editorView.value.dispatch(options.editorView.value.state.update({ 
        changes: { from: pos, to: pos, insert: mdFileText },
        selection: { anchor: pos! + mdFileText.length },
      }));
    } finally {
      fileUploadInProgress.value = false;
    }
  }
  
  function onBeforeApplyRemoteTextChange(event: any) {
    if (options.editorView.value && event.path === options.props.value.collab?.path) {
      options.editorView.value.dispatch(options.editorView.value.state.update({
        changes: event.changes,
        annotations: [
          Transaction.addToHistory.of(false),
          Transaction.remote.of(true),
        ]
      }));
    }
  }

  const editorState = shallowRef<EditorState|null>(null);
  const editorActions = ref<{[key: string]: (enabled: boolean) => void}>({});
  const eventBusBeforeApplyRemoteTextChanges = useEventBus('collab:beforeApplyRemoteTextChanges');

  function createEditorStateConfig() {
    return {
      doc: valueNotNull.value,
      extensions: [
        ...options.extensions,
        history(),
        keymap.of([...defaultKeymap, ...historyKeymap]),
        tooltips({ parent: document.body }),
        EditorView.domEventHandlers({
          blur: (event: FocusEvent) => options.emit('blur', event),
          focus: (event: FocusEvent) => options.emit('focus', event),
        }),
        EditorView.updateListener.of((viewUpdate: ViewUpdate) => {
          editorState.value = viewUpdate.state;
          
          // https://discuss.codemirror.net/t/codemirror-6-proper-way-to-listen-for-changes/2395/11
          if (viewUpdate.docChanged && viewUpdate.state.doc.toString() !== valueNotNull.value) {
            // Collab updates
            if (options.props.value.collab) {
              for (const tr of viewUpdate.transactions) {
                if (tr.docChanged && !tr.annotation(Transaction.remote)) {
                  options.emit('collab', {
                    type: CollabEventType.UPDATE_TEXT,
                    path: options.props.value.collab.path,
                    updates: [{ changes: tr.changes, selection: tr.selection }],
                  });
                }
              }
            }

            // Model-value updates
            options.emit('update:modelValue', viewUpdate.state.doc.toString());
          }

          if (options.props.value.collab && (viewUpdate.selectionSet || viewUpdate.focusChanged)) {
            // Collab awareness updates
            const hasFocus = options.editorView.value?.hasFocus || false;
            options.emit('collab', {
              type: CollabEventType.AWARENESS,
              path: options.props.value.collab.path,
              focus: hasFocus,
              selection: viewUpdate.state.selection,
            });
          }
        }),
        remoteSelection(),
      ]
    };
  }

  watch(options.editorView, (newValue, oldValue) => {
    // Post-init EditorView
    if (options.editorView.value && newValue && !oldValue) {
      eventBusBeforeApplyRemoteTextChanges.on(onBeforeApplyRemoteTextChange);

      editorState.value = options.editorView.value.state;
      editorActions.value = {
        disabled: createEditorExtensionToggler(options.editorView.value, [
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
        ]),
        spellcheckLanguageTool: createEditorExtensionToggler(options.editorView.value, [
          spellcheck({
            performSpellcheckRequest,
            performSpellcheckAddWordRequest,
          }),
          spellcheckTheme,
        ]),
        spellcheckBrowser: createEditorExtensionToggler(options.editorView.value, [
          EditorView.contentAttributes.of({ spellcheck: "true" }),
        ]),
        uploadFile: createEditorExtensionToggler(options.editorView.value, [
          EditorView.domEventHandlers({
            drop: (event: DragEvent) => {
              event.stopPropagation();
              event.preventDefault();
              const dropPos = options.editorView.value!.posAtCoords({ x: event.clientX, y: event.clientY });
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
        darkTheme: createEditorExtensionToggler(options.editorView.value, [
          EditorView.theme({}, { dark: true }),
        ]),
      };
      editorActions.value.disabled(Boolean(options.props.value.disabled || options.props.value.readonly));
      editorActions.value.spellcheckLanguageTool(spellcheckLanguageToolEnabled.value);
      editorActions.value.spellcheckBrowser(spellcheckBrowserEnabled.value);
      editorActions.value.uploadFile(fileUploadEnabled.value);
      editorActions.value.darkTheme(theme.current.value.dark);
    } else if (!newValue) {
      eventBusBeforeApplyRemoteTextChanges.off(onBeforeApplyRemoteTextChange);
    }
  }, { immediate: true });
  onBeforeUnmount(() => {
    eventBusBeforeApplyRemoteTextChanges.off(onBeforeApplyRemoteTextChange);
  })

  function onIntersect(isIntersecting: boolean) {
    if (isIntersecting) {
      editorWasInView.value = true;
    }
  }

  watch(valueNotNull, () => {
    if (options.editorView.value && valueNotNull.value !== options.editorView.value.state.doc.toString()) {
      options.editorView.value.dispatch(options.editorView.value.state.update({
        changes: {
          from: 0,
          to: options.editorView.value.state.doc.length,
          insert: valueNotNull.value,
        },
      }));
    }
  });
  watch([() => options.props.value.disabled, () => options.props.value.readonly], () => {
    const readonly = Boolean(options.props.value.disabled || options.props.value.readonly)
    editorActions.value.disabled?.(readonly);
  });
  watch(() => options.props.value.lang, () => {
    if (spellcheckLanguageToolEnabled.value && options.editorView.value) {
      forceLinting(options.editorView.value);
    }
  });
  watch(spellcheckLanguageToolEnabled, (val) => {
    editorActions.value?.spellcheckLanguageTool(val);
    if (!val && options.editorView.value) {
    // clear existing spellcheck items from editor
      options.editorView.value.dispatch(setDiagnostics(options.editorView.value.state, []));
    }
  });
  watch(spellcheckBrowserEnabled, val => editorActions.value.spellcheckBrowser?.(val));
  watch(theme.current, val => editorActions.value.darkTheme?.(val.dark));

  watch([() => options.props.value.collab?.clients, () => options.editorView.value], () => {
    if (!options.editorView.value) {
      return;
    }
    const remoteClients = (options.props.value.collab?.clients || []).filter(c => !c.isSelf && c.selection).map(c => ({
      client_id: c.client_id,
      color: c.client_color,
      name: c.user.username + (c.user.name ? ` (${c.user.name})` : ''),
      selection: c.selection!,
    }));

    options.editorView.value.dispatch({
      effects: [
        setRemoteClients.of(remoteClients)
      ]
    })
  });

  function focus() {
    if (options.editorView.value) {
      options.editorView.value.focus();
      options.emit('focus');
    }
  }
  function blur() {
    if (options.editorView.value) {
      options.editorView.value.dom.blur();
    }
  }

  const markdownToolbarAttrs = computed(() => ({
    editorView: options.editorView.value,
    editorState: editorState.value,
    disabled: options.props.value.disabled || options.props.value.readonly,
    uploadFiles: fileUploadEnabled.value ? uploadFiles : undefined,
    fileUploadInProgress: fileUploadInProgress.value,
    lang: options.props.value.lang,
    spellcheckEnabled: options.props.value.spellcheckEnabled,
    'onUpdate:spellcheckEnabled': (val: boolean) => options.emit('update:spellcheckEnabled', val),
    markdownEditorMode: options.props.value.markdownEditorMode,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => options.emit('update:markdownEditorMode', val),
  }));
  const markdownStatusbarAttrs = computed(() => ({
    editorState: editorState.value!,
    fileUploadEnabled: fileUploadEnabled.value,
    fileUploadInProgress: fileUploadInProgress.value,
  }));
  const markdownPreviewAttrs = computed(() => ({
    value: options.props.value.modelValue,
    rewriteFileUrl: options.props.value.rewriteFileUrl,
    rewriteReferenceLink: options.props.value.rewriteReferenceLink,
    cacheBuster: previewCacheBuster,
  }));

  return {
    editorView: options.editorView,
    editorState,
    createEditorStateConfig,
    editorActions,
    markdownToolbarAttrs,
    markdownStatusbarAttrs,
    markdownPreviewAttrs,
    onIntersect,
    focus,
    blur,
  }
}

export function useMarkdownEditor(options: {
    extensions: Extension[];
    props: ComputedRef<MarkdownProps & {
        modelValue: string|null;
        disabled?: boolean;
        readonly?: boolean;
        spellcheckSupported?: boolean;
    }>;
    emit: any;
    fileUploadSupported: boolean;
}) {
  const vm = getCurrentInstance()!;
  const editorRef = computed(() => vm.refs.editorRef as HTMLElement);
  const editorView = shallowRef<EditorView|null>(null);
  
  const mdBase = useMarkdownEditorBase({
    ...options,
    editorView,
  });
  
  function initializeEditorView() {
    editorView.value = new EditorView({
      parent: editorRef.value,
      state: EditorState.create(mdBase.createEditorStateConfig()),
    });
  }
  onMounted(() => initializeEditorView());
  onBeforeUnmount(() => {
    editorView.value?.destroy();
  });

  return mdBase;
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
  ] as Extension[];
}

export function markdownEditorPageExtensions() {
  return [
    ...markdownEditorDefaultExtensions(),
    scrollPastEnd(),
  ] as Extension[];
}
