import urlJoin from "url-join";
import { formatISO9075 } from "date-fns";
import { v4 as uuid4 } from 'uuid';
import {
  createEditorExtensionToggler,
  MergeView, EditorView, EditorState,
  // @ts-ignore
} from "reportcreator-markdown/editor";
import { MarkdownEditorMode } from '@/utils/types';

export type DiffFieldProps = {
  value?: any;
  definition?: FieldDefinition|null;
  selectableUsers?: UserShortInfo[];
  markdownEditorMode?: MarkdownEditorMode;
  'onUpdate:markdownEditorMode'?: (val: MarkdownEditorMode) => void;
  rewriteFileUrl?: (fileSrc: string) => string;
  rewriteReferenceLink?: (src: string) => {href: string, title: string}|null;
};

export function useMarkdownDiff({ props, extensions }: {
  extensions: any[];
  props: ComputedRef<{
    historic: DiffFieldProps,
    current: DiffFieldProps,
  }>;
}) {
  const theme = useTheme();
  const previewCacheBuster = uuid4();

  const valueNotNullHistoric = computed(() => props.value.historic.value || '');
  const valueNotNullCurrent = computed(() => props.value.current.value || '');

  const vm = getCurrentInstance()!;
  const mergeRef = computed(() => vm.refs.mergeRef);
  const mergeView = shallowRef<MergeView|null>(null);
  const editorActions = ref<{[key: string]: (enabled: boolean) => void}>({});
  function initializeMergeView() {
    mergeView.value = new MergeView({
      parent: mergeRef.value,
      root: document,
      orientation: "a-b",
      highlightChanges: true,
      gutter: true,
      a: {
        doc: valueNotNullHistoric.value,
        extensions: [
          ...extensions,
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
        ]
      },
      b: {
        doc: valueNotNullCurrent.value,
        extensions: [
          ...extensions,
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
        ]
      },
    });
    editorActions.value = {
      darkThemeA: createEditorExtensionToggler(mergeView.value.a, [
        EditorView.theme({}, { dark: true }),
      ]),
      darkThemeB: createEditorExtensionToggler(mergeView.value.b, [
        EditorView.theme({}, { dark: true }),
      ]),
    };
    editorActions.value.darkThemeA(theme.current.value.dark);
    editorActions.value.darkThemeB(theme.current.value.dark);
  }
  onMounted(() => initializeMergeView());
  onBeforeUnmount(() => {
    if (mergeView.value) {
      mergeView.value.destroy();
    }
  });

  watch(valueNotNullHistoric, () => {
    if (mergeView.value && valueNotNullHistoric.value !== mergeView.value.a.state.doc.toString()) {
      mergeView.value.a.dispatch({
        changes: {
          from: 0,
          to: mergeView.value.a.state.doc.length,
          insert: valueNotNullHistoric.value,
        }
      });
    }
  })
  watch(valueNotNullCurrent, () => {
    if (mergeView.value && valueNotNullCurrent.value !== mergeView.value.b.state.doc.toString()) {
      mergeView.value.b.dispatch({
        changes: {
          from: 0,
          to: mergeView.value.b.state.doc.length,
          insert: valueNotNullCurrent.value,
        }
      });
    }
  });

  watch(theme.current, (val) => {
    editorActions.value.darkThemeA?.(val.dark);
    editorActions.value.darkThemeB?.(val.dark);
  });

  const markdownToolbarAttrs = computed(() => ({
    disabled: true,
    markdownEditorMode: props.value.historic.markdownEditorMode,
    'onUpdate:markdownEditorMode': props.value.historic['onUpdate:markdownEditorMode'],
  }));
  const markdownPreviewAttrsHistoric = computed(() => ({
    value: valueNotNullHistoric.value,
    rewriteFileUrl: props.value.historic.rewriteFileUrl,
    rewriteReferenceLink: props.value.historic.rewriteReferenceLink,
    cacheBuster: previewCacheBuster,
  }));
  const markdownPreviewAttrsCurrent = computed(() => ({
    value: valueNotNullCurrent.value,
    rewriteFileUrl: props.value.current.rewriteFileUrl,
    rewriteReferenceLink: props.value.current.rewriteReferenceLink,
    cacheBuster: previewCacheBuster,
  }));

  return {
    mergeView,
    markdownToolbarAttrs,
    markdownPreviewAttrsHistoric,
    markdownPreviewAttrsCurrent,
  }
}

export async function useProjectHistory<T>(options: {
  subresourceUrlPart: string;
}) {
  const route = useRoute();
  const projectStore = useProjectStore();
  const projectTypeStore = useProjectTypeStore();

  const projectUrlCurrent = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/`);
  const projectUrlHistoric = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/`);

  // TODO: error handling => show error in frontend instead of crashing => useFetch like in lockedit
  const fetchState = await useAsyncDataE(async () => {
    const [projectCurrent, projectHistoric, dataCurrent, dataHistoric] = await Promise.all([
      projectStore.getById(route.params.projectId as string),
      $fetch<PentestProject>(projectUrlHistoric.value, { method: 'GET' }),
      $fetch<T>(urlJoin(projectUrlCurrent.value, options.subresourceUrlPart), { method: 'GET' }).catch(() => null),
      $fetch<T>(urlJoin(projectUrlHistoric.value, options.subresourceUrlPart), { method: 'GET' }),
    ]);

    const [projectTypeCurrent, projectTypeHistoric] = await Promise.all([
      projectTypeStore.getById(projectCurrent.project_type),
      $fetch<ProjectType>(`/api/v1/projecttypes/${projectHistoric.project_type}/history/${route.params.historyDate}/`),
    ]);
    return {
      projectCurrent,
      projectHistoric,
      dataCurrent,
      dataHistoric,
      projectTypeCurrent,
      projectTypeHistoric,
    };
  }, { key: `projectHistory-${route.params.projectId}-${route.params.historyDate}-${options.subresourceUrlPart}` });

  const projectTypeUrlCurrent = computed(() => `/api/v1/projecttypes/${fetchState.value.projectCurrent.project_type}/`);
  const projectTypeUrlHistoric = computed(() => `/api/v1/projecttypes/${fetchState.value.projectHistoric.project_type}/history/${route.params.historyDate}/`);
  function rewriteFileUrlCurrent(fileSrc: string) {
    if (fileSrc.startsWith('/assets/')) {
      return urlJoin(projectTypeUrlCurrent.value || '', fileSrc)
    } else {
      return urlJoin(projectUrlCurrent.value, fileSrc);
    }
  }
  function rewriteFileUrlHistoric(fileSrc: string) {
    if (fileSrc.startsWith('/assets/')) {
      return urlJoin(projectTypeUrlHistoric.value || '', fileSrc)
    } else {
      return urlJoin(projectUrlHistoric.value, fileSrc);
    }
  }

  function rewriteReferenceLink(refId: string) {
    const finding = projectStore.findings(fetchState.value.projectCurrent.id || '').find(f => f.id === refId);
    if (finding) {
      return {
        href: `/projects/${fetchState.value!.projectCurrent.id}/reporting/findings/${finding.id}/`,
        title: `[Finding ${finding.data.title}]`,
      };
    }
    return null;
  }

  const markdownEditorMode = ref(MarkdownEditorMode.MARKDOWN);
  watch(markdownEditorMode, (val) => {
    // Skip side-by-side view. There is not much space for it.
    if (val === MarkdownEditorMode.MARKDOWN_AND_PREVIEW) {
      markdownEditorMode.value = MarkdownEditorMode.PREVIEW;
    }
  });

  const fieldAttrsCurrent = computed(() => ({
    lang: fetchState.value.projectCurrent.language || 'en-US',
    selectableUsers: [...fetchState.value.projectCurrent.members, ...fetchState.value.projectCurrent.imported_members],
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    rewriteFileUrl: rewriteFileUrlCurrent,
    rewriteReferenceLink,
  }));
  const fieldAttrsHistoric = computed(() => ({
    lang: fetchState.value.projectHistoric.language || 'en-US',
    selectableUsers: [...fetchState.value.projectHistoric.members, ...fetchState.value.projectHistoric.imported_members],
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    rewriteFileUrl: rewriteFileUrlHistoric,
    rewriteReferenceLink,
  }));

  const toolbarAttrs = computed(() => ({
    ref: 'toolbarRef',
    data: fetchState.value.dataHistoric,
    editMode: EditMode.READONLY,
    errorMessage: `This is a historical version from ${formatISO9075(new Date(route.params.historyDate as string))}.`,
  }));

  return {
    fetchState,
    obj: computed(() => fetchState.value.dataHistoric),
    toolbarAttrs,
    fieldAttrsCurrent,
    fieldAttrsHistoric,
  }
}
