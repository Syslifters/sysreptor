import urlJoin from "url-join";
import pick from "lodash/pick";
import { formatISO9075 } from "date-fns";
import {
  MergeView, EditorView,
} from "reportcreator-markdown/editor";
import { MarkdownEditorMode, type FieldDefinitionDict } from '@/utils/types';

export type DiffFieldProps = {
  value?: any;
  definition?: FieldDefinition|null;
  collab?: CollabPropType;
  readonly?: boolean;
  selectableUsers?: UserShortInfo[];
  'onUpdate:markdownEditorMode'?: (val: MarkdownEditorMode) => void;
  'onUpdate:spellcheckEnabled'?: (val: boolean) => void;
  'onCollab'?: (val: any) => void;
} & MarkdownProps;

export type DynamicInputFieldDiffProps = {
  id: string;
  nestingLevel?: number;
  historic: DiffFieldProps;
  current: DiffFieldProps;
}

export function useMarkdownDiff(options: {
  extensions: any[];
  props: ComputedRef<{
    historic: DiffFieldProps,
    current: DiffFieldProps,
  }>;
}) {
  const vm = getCurrentInstance()!;
  const mergeViewRef = computed(() => vm.refs.mergeViewRef as HTMLElement);
  const mergeView = shallowRef<MergeView|null>(null);

  const editorViewCurrent = shallowRef<EditorView|null>(null);
  const editorViewHistoric = shallowRef<EditorView|null>(null);
  const mdBaseCurrent = useMarkdownEditorBase({
    editorView: editorViewCurrent,
    extensions: options.extensions,
    props: computed(() => ({
      modelValue: options.props.value.current.value,
      ...pick(options.props.value.current, ['collab', 'lang', 'readonly', 'disabled', 'markdownEditorMode', 'spellcheckEnabled', 'uploadFile', 'rewriteFileUrl', 'rewriteReferenceLink']),
    })),
    emit: (name: string, value: any) => {
      const emit = (options.props.value.current as any)['on' + name.charAt(0).toUpperCase() + name.slice(1)];
      if (typeof emit === 'function') {
        emit(value);
      }
    },
    fileUploadSupported: true,
  });
  const mdBaseHistoric = useMarkdownEditorBase({
    editorView: editorViewHistoric,
    extensions: options.extensions,
    props: computed(() => ({
      modelValue: options.props.value.historic.value,
      readonly: true,
      ...pick(options.props.value.historic, ['lang', 'markdownEditorMode', 'rewriteFileUrl', 'rewriteReferenceLink']),
    })),
    emit: (name: string, value: any) => {
      const emit = (options.props.value.historic as any)['on' + name.charAt(0).toUpperCase() + name.slice(1)];
      if (typeof emit === 'function') {
        emit(value);
      }
    },
    fileUploadSupported: false,
  });

  function initializeMergeView() {
    mergeView.value = new MergeView({
      parent: mergeViewRef.value,
      root: document,
      orientation: "a-b",
      revertControls: "a-to-b",
      highlightChanges: true,
      gutter: true,
      a: mdBaseHistoric.createEditorStateConfig(),
      b: mdBaseCurrent.createEditorStateConfig(),
    });
    editorViewHistoric.value = mergeView.value.a;
    editorViewCurrent.value = mergeView.value.b;
  }
  onMounted(() => initializeMergeView());
  onBeforeUnmount(() => {
    mergeView.value?.destroy();
  });

  return {
    mergeView,
    markdownToolbarAttrs: mdBaseCurrent.markdownToolbarAttrs,
    markdownPreviewAttrsHistoric: mdBaseHistoric.markdownPreviewAttrs,
    markdownPreviewAttrsCurrent: mdBaseCurrent.markdownPreviewAttrs,
  }
}

export function formatHistoryObjectFieldProps(options: {
  historic: {
    value?: any;
    definition?: FieldDefinitionDict;
    fieldIds: string[];
    attrs?: any;
  },
  current: {
    value?: any;
    definition?: FieldDefinitionDict;
    fieldIds: string[];
    attrs?: any;
  },
  attrs?: any;
}) {
  const out = [] as DynamicInputFieldDiffProps[];
  for (const fieldId of options.historic.fieldIds.concat(options.current.fieldIds)) {
    if (!out.some(f => f.id === fieldId)) {
      out.push({
        id: fieldId,
        historic: {
          value: options.historic.value?.[fieldId],
          definition: options.historic.definition?.[fieldId],
          ...options.historic.attrs,
        },
        current: {
          value: options.current.value?.[fieldId],
          definition: options.current.definition?.[fieldId],
          ...options.current.attrs,
        },
        ...options.attrs,
      });
    }
  }
  return out;
}

export function useProjectHistory<T>(options: {
  subresourceUrlPart: string;
}) {
  const route = useRoute();
  const projectStore = useProjectStore();
  const projectTypeStore = useProjectTypeStore();

  const projectUrlCurrent = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/`);
  const projectUrlHistoric = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/`);

  const fetchState = useLazyAsyncData(async () => {
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
  });

  const projectTypeUrlCurrent = computed(() => `/api/v1/projecttypes/${fetchState.data.value?.projectCurrent.project_type}/`);
  const projectTypeUrlHistoric = computed(() => `/api/v1/projecttypes/${fetchState.data.value?.projectHistoric.project_type}/history/${route.params.historyDate}/`);
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
    const finding = projectStore.findings(fetchState.data.value?.projectCurrent.id || '').find(f => f.id === refId);
    if (finding) {
      return {
        href: `/projects/${fetchState.data.value?.projectCurrent.id}/reporting/findings/${finding.id}/`,
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
    lang: fetchState.data.value?.projectCurrent.language || 'en-US',
    selectableUsers: [...(fetchState.data.value?.projectCurrent.members || []), ...(fetchState.data.value?.projectCurrent.imported_members || [])],
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    rewriteFileUrl: rewriteFileUrlCurrent,
    rewriteReferenceLink,
  }));
  const fieldAttrsHistoric = computed(() => ({
    lang: fetchState.data.value?.projectHistoric.language || 'en-US',
    selectableUsers: [...(fetchState.data.value?.projectHistoric.members || []), ...(fetchState.data.value?.projectHistoric.imported_members || [])],
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    rewriteFileUrl: rewriteFileUrlHistoric,
    rewriteReferenceLink,
  }));

  const toolbarAttrs = computed(() => ({
    ref: 'toolbarRef',
    data: fetchState.data.value?.dataHistoric,
    editMode: EditMode.READONLY,
    errorMessage: `You are comparing a historic version from ${formatISO9075(new Date(route.params.historyDate as string))} to the current version.`,
  }));
  const fetchLoaderAttrs = computed(() => ({
    fetchState: {
      data: fetchState.data.value,
      error: fetchState.error.value,
      pending: fetchState.pending.value,
    },
  }));

  return {
    fetchState,
    obj: computed(() => fetchState.data.value?.dataHistoric),
    toolbarAttrs,
    fieldAttrsCurrent,
    fieldAttrsHistoric,
    fetchLoaderAttrs,
  }
}
