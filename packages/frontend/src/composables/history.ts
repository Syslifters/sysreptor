import { pick, get, trim } from "lodash-es";
import {
  MergeView, type EditorView,
} from "@sysreptor/markdown/editor";
import { MarkdownEditorMode, type FieldDefinition, type PentestProject, type ProjectType } from '#imports';
import { urlJoin } from "@base/utils/helpers";

export type DiffFieldProps = {
  value?: any;
  definition?: FieldDefinition|null;
  collab?: CollabPropType;
  readonly?: boolean;
  selectableUsers?: UserShortInfo[];
  'onUpdate:markdownEditorMode'?: (val: MarkdownEditorMode) => void;
  'onUpdate:spellcheckEnabled'?: (val: boolean) => void;
  'onCollab'?: (val: any) => void;
  'onComment'?: (val: any) => void;
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
      ...pick(options.props.value.current, [
        'collab', 'lang', 'readonly', 'disabled', 'markdownEditorMode', 'spellcheckSupported', 'spellcheckEnabled', 
        'referenceItems', 'uploadFile', 'rewriteFileUrl',
      ]),
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
      ...pick(options.props.value.historic, ['lang', 'markdownEditorMode', 'rewriteFileUrl', 'referenceItems']),
    })),
    emit: (name: string, value: any) => {
      const emit = (options.props.value.historic as any)['on' + name.charAt(0).toUpperCase() + name.slice(1)];
      if (typeof emit === 'function') {
        emit(value);
      }
    },
    fileUploadSupported: false,
  });
  const markdownToolbarAttrs = computed(() => ({
    ...mdBaseCurrent.markdownToolbarAttrs.value,
    hideSplitMode: true,
  }));

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
    markdownToolbarAttrs,
    markdownPreviewAttrsHistoric: mdBaseHistoric.markdownPreviewAttrs,
    markdownPreviewAttrsCurrent: mdBaseCurrent.markdownPreviewAttrs,
  }
}

export function formatHistoryObjectFieldProps(options: {
  id?: string;
  historic: {
    value?: any;
    definition?: FieldDefinition[];
    attrs?: any;
  },
  current: {
    value?: any;
    definition?: FieldDefinition[];
    attrs?: any;
  },
  attrs?: any;
}) {
  const out = [] as DynamicInputFieldDiffProps[];
  for (const fieldId of (options.historic.definition?.map(f => f.id) || []).concat(options.current.definition?.map(f => f.id) || [])) {
    if (!out.some(f => f.id === fieldId)) {
      out.push({
        ...options.attrs,
        id: options.id ? `${options.id}.${fieldId}` : fieldId,
        historic: {
          ...options.historic.attrs,
          value: options.historic.value?.[fieldId],
          definition: options.historic.definition?.find(f => f.id === fieldId),
        },
        current: {
          ...options.current.attrs,
          value: options.current.value?.[fieldId],
          definition: options.current.definition?.find(f => f.id === fieldId),
          collab: options.current.attrs?.collab ? collabSubpath(options.current.attrs.collab, fieldId) : undefined,
        },
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
  const dataCurrent = computedThrottled<T|null>(() => get(collab.data.value, trim(options.subresourceUrlPart.replaceAll('/', '.'), '.')) || null, { throttle: 500 });

  const markdownEditorMode = ref(MarkdownEditorMode.MARKDOWN);
  const spellcheckEnabled = options.spellcheckEnabled || ref(false);

  const projectEditBaseHistoric = useProjectEditBase({
    project: computed(() => fetchState.value.projectHistoric),
    projectType: computed(() => fetchState.value.projectTypeHistoric),
    historyDate: route.params.historyDate as string,
    markdownEditorMode,
    spellcheckEnabled,
  });
  const projectEditBaseCurrent = useProjectEditBase({
    project: computed(() => fetchState.value.projectCurrent),
    projectType: computed(() => fetchState.value.projectTypeCurrent),
    markdownEditorMode,
    spellcheckEnabled,
  })

  const fieldAttrsCurrent = computed(() => ({
    ...projectEditBaseCurrent.inputFieldAttrs.value,
    readonly: collab.readonly.value || !dataCurrent.value, // no edit permission or viewing deleted object
    collab: collab.collabProps.value,
    onCollab: collab.onCollabEvent,
  }));
  const fieldAttrsHistoric = computed(() => ({
    ...projectEditBaseHistoric.inputFieldAttrs.value,
    readonly: true,
  }));

  const toolbarAttrs = computed(() => ({
    ref: 'toolbarRef',
    data: fetchState.value.dataHistoric,
    errorMessage: projectEditBaseCurrent.errorMessage.value,
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
