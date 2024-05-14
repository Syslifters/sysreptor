import urlJoin from "url-join";
import pick from "lodash/pick";
import get from "lodash/get";
import trim from "lodash/trim";
import { formatISO9075 } from "date-fns";
import {
  MergeView, EditorView,
} from "reportcreator-markdown/editor";
import { MarkdownEditorMode, type FieldDefinitionDict, type PentestProject } from '@/utils/types';

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
      revertControls: options.props.value.current.readonly ? undefined : "a-to-b",
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

  watch(() => options.props.value.current.readonly, (readonly) => {
    mergeView.value?.reconfigure({ revertControls: readonly ? undefined : "a-to-b" });
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
          ...options.historic.attrs,
          value: options.historic.value?.[fieldId],
          definition: options.historic.definition?.[fieldId],
        },
        current: {
          ...options.current.attrs,
          value: options.current.value?.[fieldId],
          definition: options.current.definition?.[fieldId],
          collab: options.current.attrs?.collab ? collabSubpath(options.current.attrs.collab, fieldId) : undefined,
        },
        ...options.attrs,
      });
    }
  }
  return out;
}

export async function useProjectHistory<T>(options: {
  subresourceUrlPart: string;
  spellcheckEnabled?: Ref<boolean>;
  useCollab: (project: PentestProject) => any;
}) {
  const route = useRoute();
  const projectStore = useProjectStore();
  const projectTypeStore = useProjectTypeStore();

  const projectUrlCurrent = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/`);
  const projectUrlHistoric = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/history/${route.params.historyDate}/`);

  const fetchState = await useAsyncDataE(async () => {
    const [projectCurrent, projectHistoric, dataHistoric] = await Promise.all([
      projectStore.getById(route.params.projectId as string),
      $fetch<PentestProject>(projectUrlHistoric.value, { method: 'GET' }),
      $fetch<T>(urlJoin(projectUrlHistoric.value, options.subresourceUrlPart), { method: 'GET' }),
    ]);

    const [projectTypeCurrent, projectTypeHistoric] = await Promise.all([
      projectTypeStore.getById(projectCurrent.project_type),
      $fetch<ProjectType>(`/api/v1/projecttypes/${projectHistoric.project_type}/history/${route.params.historyDate}/`),
    ]);
    return {
      projectCurrent,
      projectHistoric,
      dataHistoric,
      projectTypeCurrent,
      projectTypeHistoric,
    };
  });
  const collab = options.useCollab(fetchState.value.projectCurrent);
  const dataCurrent = computed<T|null>(() => get(collab.data.value, trim(options.subresourceUrlPart.replaceAll('/', '.'), '.')) || null);

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
        href: `/projects/${fetchState.value.projectCurrent.id}/reporting/findings/${finding.id}/`,
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
  const spellcheckEnabled = options.spellcheckEnabled || ref(false);

  const fieldAttrsCurrent = computed(() => ({
    readonly: collab.readonly.value || !dataCurrent.value, // no edit permission or viewing deleted object
    collab: collab.collabProps.value,
    onCollab: collab.onCollabEvent,
    lang: fetchState.value.projectCurrent.language || 'en-US',
    selectableUsers: [...(fetchState.value.projectCurrent.members || []), ...(fetchState.value.projectCurrent.imported_members || [])],
    markdownEditorMode: markdownEditorMode.value,
    spellcheckEnabled: spellcheckEnabled.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    'onUpdate:spellcheckEnabled': (val: boolean) => { spellcheckEnabled.value = val; },
    rewriteFileUrl: rewriteFileUrlCurrent,
    rewriteReferenceLink,
  }));
  const fieldAttrsHistoric = computed(() => ({
    lang: fetchState.value.projectHistoric.language || 'en-US',
    selectableUsers: [...(fetchState.value.projectHistoric.members || []), ...(fetchState.value.projectHistoric.imported_members || [])],
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    rewriteFileUrl: rewriteFileUrlHistoric,
    rewriteReferenceLink,
  }));

  const toolbarAttrs = computed(() => ({
    ref: 'toolbarRef',
    data: fetchState.value.dataHistoric,
    editMode: EditMode.READONLY,
    errorMessage: `You are comparing a historic version from ${formatISO9075(new Date(route.params.historyDate as string))} to the current version.`,
  }));

  return {
    fetchState: computed(() => ({
      ...fetchState.value,
      dataCurrent: dataCurrent.value,
    })),
    obj: computed(() => fetchState.value.dataHistoric),
    toolbarAttrs,
    fieldAttrsCurrent,
    fieldAttrsHistoric,
    collab,
  }
}

// TODO: collaborative editing in history
// * [x] markdown
//  * [x] markdown: merge editor
//  * [x] propagate collab events
//  * [x] disable merge if readonly => reconfigure({ revertControls: undefined })
// * [x] pages: use collab
//  * [x] note history
//  * [x] finding history
//  * [x] section history
// * [x] useProjectHistory
//  * [x] use collab
//  * [x] handle finding deleted in current version
//  * [x] if deleted: set readonly
// * [ ] DynamicInputField
//  * [x] pass collab props
//  * [x] do not disable unchanged fields
//  * [ ] how to handle lists in UI => add/delete actions ???
// * [ ] UI:
//  * [ ] show finding/note list item as selected
//  * [ ] loading animation for history pages
// * [ ] tests (manual)
//  * [ ] collaborative editing in markdown/string fields
//  * [ ] collaborative editing in notes, findings, sections
//  * [ ] finished project: readonly
//  * [ ] read-only mode in templates
//  * [ ] unchanged fields are editable => not disabled
