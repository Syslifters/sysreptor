import urlJoin from "url-join";
import cloneDeep from "lodash/cloneDeep";
import { onBeforeRouteLeave, onBeforeRouteUpdate } from "vue-router";
import type { VForm } from "vuetify/lib/components/index.mjs";
import { formatISO9075 } from "date-fns";
import {
  EditMode,
  ProjectTypeScope,
  UploadedFileType,
  MarkdownEditorMode,
} from "~/utils/types";
import type {
  PentestProject,
  ProjectType,
  UploadedFileInfo,
} from "~/utils/types";
import { EditToolbar } from "#components";

export type ToolbarRef = Ref<InstanceType<typeof EditToolbar>>|ComputedRef<InstanceType<typeof EditToolbar>>;
export type LockEditOptions<T> = {
  toolbarRef?: ToolbarRef;
  data: Ref<T>;
  baseUrl?: ComputedRef<string|null>;
  form?: Ref<VForm|undefined>;
  fetchState?: ReturnType<typeof useLazyFetch>;
  hasEditPermissions?: ComputedRef<boolean>;
  canDelete?: ComputedRef<boolean>;
  errorMessage?: ComputedRef<string|null>;
  deleteConfirmInput?: ComputedRef<string|null>;
  performSave?: (data: T) => Promise<any>;
  performDelete?: (data: T) => Promise<any>;
  updateInStore?: (data: T) => void;
  autoSaveOnUpdateData?: (event: { oldValue: T; newValue: T }) => boolean;
}

export function useLockEdit<T>(options: LockEditOptions<T>) {
  const route = useRoute();
  const vm = getCurrentInstance()!;
  const toolbarRef = options.toolbarRef || computed(() => vm.refs.toolbarRef);
  const lockUrl = computed(() => options.baseUrl?.value ? urlJoin(options.baseUrl.value, '/lock/') : undefined);
  const unlockUrl = computed(() => options.baseUrl?.value ? urlJoin(options.baseUrl.value, '/unlock/') : undefined);
  const hasEditPermissions = computed(() => {
    if (options.hasEditPermissions) {
      return options.hasEditPermissions.value;
    }
    return true;
  });
  const editMode = ref<EditMode>(hasEditPermissions?.value ? EditMode.EDIT : EditMode.READONLY);
  const readonly = computed(() => editMode.value === EditMode.READONLY);
  watch(hasEditPermissions, (val) => {
    if (!val) {
      editMode.value = EditMode.READONLY;
    }
  });
  const data = computed(() => {
    if (options.fetchState && options.fetchState.pending.value) {
      return null;
    }
    return options.data.value;
  });

  const navigationInProgress = ref(false);
  onBeforeRouteLeave(async (to, from, next) => {
    if (toolbarRef.value) {
      await toolbarRef.value.beforeLeave(to, from, (res = true) => {
        navigationInProgress.value = res;
      });
      await nextTick();
      next(navigationInProgress.value);
    } else {
      next();
    }
  });
  onBeforeRouteUpdate(async (to, from, next) => {
    if (toolbarRef.value && to.path !== from.path) {
      await toolbarRef.value.beforeLeave(to, from, (res = true) => {
        navigationInProgress.value = res;
      });
      await nextTick();
      next(navigationInProgress.value);
    } else {
      next();
    }
  });

  const fetchLoaderAttrs = computed(() => {
    return {
      fetchState: {
        data: options.fetchState?.data.value,
        error: options.fetchState?.error.value,
        pending: options.fetchState?.pending.value || navigationInProgress.value,
      }
    };
  });
  onMounted(() => {
    if (options.updateInStore && data.value) {
      // Set initial value in store to update lock info
      options.updateInStore(cloneDeep(data.value));
    }
  })
  watch(() => options.fetchState?.pending.value, async (val) => {
    if (!val && data.value) {
      if (options.updateInStore) {
        options.updateInStore(cloneDeep(data.value));
      }

      // Scroll to element
      await nextTick();
      if (route.hash) {
        const el = document.getElementById(route.hash.substring(1));
        if (el) {
          el.scrollIntoView();
        }
      }
    }
  });
  async function onUpdateData(event: { oldValue: T|null, newValue: T|null }) {
    if (options.autoSaveOnUpdateData &&
      event.oldValue && event.newValue &&
      toolbarRef.value?.autoSaveEnabled &&
      options.autoSaveOnUpdateData({ oldValue: event.oldValue!, newValue: event.newValue! })
    ) {
      await toolbarRef.value.performSave();
    }
  }

  const errorMessage = computed(() => {
    if (hasEditPermissions.value) {
      return null;
    }
    if (options.errorMessage?.value) {
      return options.errorMessage.value
    }
    return 'You do not have permissions to edit this resource.';
  })
  const toolbarAttrs = computed(() => {
    return ({
      ref: 'toolbarRef',
      data: data.value,
      'onUpdate:data': onUpdateData,
      'onUpdate:lockedData': options.updateInStore,
      editMode: editMode.value,
      'onUpdate:editMode': (val: EditMode) => { editMode.value = val; },
      errorMessage: errorMessage.value,
      ...((options.performSave) ? {
        save: options.performSave,
        lockUrl: lockUrl.value,
        unlockUrl: unlockUrl.value,
        form: options.form?.value,
        ...(hasEditPermissions.value ? {
          canSave: hasEditPermissions.value,
        } : {}),
      } : {}),
      ...((options.performDelete) ? {
        delete: options.performDelete,
        deleteConfirmInput: options.deleteConfirmInput?.value,
        ...(options.canDelete ? {
          canDelete: options.canDelete.value,
        } : {}),
      } : {}),
    });
  });

  return {
    toolbarAttrs,
    readonly,
    fetchLoaderAttrs,
    editMode,
  };
}

export function useProjectTypeLockEdit(options: {
  projectType: Ref<ProjectType>,
  performSave?: (data: ProjectType) => Promise<void>;
  performDelete?: (data: ProjectType) => Promise<void>;
}) {
  const auth = useAuth();
  const projectType = computed(() => options.projectType.value);

  const baseUrl = computed(() => `/api/v1/projecttypes/${projectType.value.id}/`);
  // const projectType = await useFetchE<ProjectType>(baseUrl.value, { method: 'GET' });
  useHeadExtended({
    title: projectType.value.name
  });

  const hasEditPermissions = computed(() => {
    return (projectType.value.scope === ProjectTypeScope.GLOBAL && auth.permissions.value.designer) ||
             (projectType.value.scope === ProjectTypeScope.PRIVATE && auth.permissions.value.private_designs) ||
             (projectType.value.scope === ProjectTypeScope.PROJECT && projectType.value.source === SourceEnum.CUSTOMIZED);
  });
  const errorMessage = computed(() => {
    if (projectType.value.scope === ProjectTypeScope.PROJECT) {
      if (projectType.value.source === SourceEnum.SNAPSHOT) {
        return `This design cannot be edited because it is a snapshot from ${projectType.value.created.split('T')[0]}.`
      } else if (projectType.value.source === SourceEnum.IMPORTED_DEPENDENCY) {
        return 'This design cannot be edited because it is an imported snapshot.';
      } else if (projectType.value.source !== SourceEnum.CUSTOMIZED) {
        return 'This design is readonly and cannot be edited.';
      }
    }
    return null;
  })

  const deleteConfirmInput = computed(() => projectType.value.name);
  return {
    ...useLockEdit<ProjectType>({
      performSave: options.performSave,
      performDelete: options.performDelete,
      deleteConfirmInput,
      data: projectType,
      baseUrl,
      hasEditPermissions,
      errorMessage,
    }),
    projectType,
  }
}

export async function useProjectTypeLockEditOptions(options: {save?: boolean, delete?: boolean, saveFields?: string[], id?: string}) {
  const route = useRoute();
  const projectTypeId = options.id || route.params.projectTypeId;
  const projectType = await useFetchE<ProjectType>(`/api/v1/projecttypes/${projectTypeId}/`, { method: 'GET' });
  const projectTypeStore = useProjectTypeStore();

  async function performSave(data: ProjectType) {
    await projectTypeStore.partialUpdate(data, options.saveFields);
  }
  async function performDelete(data: ProjectType) {
    await projectTypeStore.delete(data);
    await navigateTo('/designs/');
  }

  return {
    projectType,
    ...(options.save ? { performSave } : {}),
    ...(options.delete ? { performDelete } : {})
  };
}

export function useProjectLockEdit<T>(options: {
  baseUrl: string;
  fetchProjectType: boolean;
  historyDate?: string;
  canUploadFiles?: boolean;
  spellcheckEnabled?: Ref<boolean>;
  markdownEditorMode?: Ref<MarkdownEditorMode>;
  performSave?: (project: PentestProject, data: T) => Promise<any>;
  performDelete?: (project: PentestProject, data: T) => Promise<any>;
  updateInStore?: (project: PentestProject, data: T) => any;
  autoSaveOnUpdateData? (options: { oldValue: T, newValue: T }): boolean;
}) {
  const route = useRoute();
  const localSettings = useLocalSettings();
  const projectStore = useProjectStore();
  const projectTypeStore = useProjectTypeStore();

  const fetchState = useLazyAsyncData(async () => {
    const [project, data] = await Promise.all([
      projectStore.getById(route.params.projectId as string),
      $fetch<T>(options.baseUrl, { method: 'GET' }),
    ]);
    const projectType = options.fetchProjectType ?
        (options.historyDate ?
            (await $fetch<ProjectType>(`/api/v1/projecttypes/${project.project_type}/history/${options.historyDate}/`)) :
            (await projectTypeStore.getById(project.project_type))
        ) :
      null;
    return {
      project,
      projectType,
      data: data as T
    };
  });

  const project = computed(() => fetchState.data.value?.project || null);
  const projectType = computed(() => fetchState.data.value?.projectType || null);
  const data = computed<T|null>({
    get: () => fetchState.data.value?.data || null,
    set: (val: T|null) => {
      if (fetchState.data.value && val) {
        fetchState.data.value.data = val;
      }
    }
  });
  const hasEditPermissions = computed(() => {
    if (options.historyDate) {
      return false;
    }
    if (project.value) {
      return !project.value?.readonly;
    }
    return true;
  });
  const errorMessage = computed(() => {
    if (options.historyDate) {
      return `This is a historical version from ${formatISO9075(new Date(options.historyDate))}.`
    }
    if (project.value?.readonly) {
      return 'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.'
    }
    return null;
  });

  const baseUrl = computed(() => options.baseUrl);
  const projectUrl = computed(() => `/api/v1/pentestprojects/${route.params.projectId}/`);
  const projectTypeUrl = computed(() => project.value ? `/api/v1/projecttypes/${project.value.project_type}/` : null);

  async function uploadFile(file: File) {
    const uploadUrl = urlJoin(projectUrl.value, options.canUploadFiles ? '/upload/' : '/images/');
    const res = await uploadFileHelper<UploadedFileInfo>(uploadUrl, file);
    if (res.resource_type === UploadedFileType.IMAGE) {
      return `![](/images/name/${res.name}){width="100%"}`;
    } else {
      return `[](/files/name/${res.name})`;
    }
  }
  function rewriteFileUrl(fileSrc: string) {
    if (fileSrc.startsWith('/assets/')) {
      return urlJoin(projectTypeUrl.value || '', fileSrc)
    } else {
      return urlJoin(projectUrl.value, fileSrc);
    }
  }
  function rewriteReferenceLink(refId: string) {
    const finding = projectStore.findings(project.value?.id || '').find(f => f.id === refId);
    if (finding) {
      return {
        href: `/projects/${project.value!.id}/reporting/findings/${finding.id}/`,
        title: `[Finding ${finding.data.title}]`,
      };
    }
    return null;
  }

  const spellcheckEnabled = options.spellcheckEnabled || computed({ 
    get: () => localSettings.reportingSpellcheckEnabled && !options.historyDate,
    set: (val: boolean) => { localSettings.reportingSpellcheckEnabled = val; }, 
  });
  const markdownEditorMode = options.markdownEditorMode || computed({
    get: () => localSettings.reportingMarkdownEditorMode,
    set: (val: MarkdownEditorMode) => { localSettings.reportingMarkdownEditorMode = val; },
  })
  const inputFieldAttrs = computed(() => ({
    lang: project.value?.language || 'en-US',
    selectableUsers: [...(project.value?.members || []), ...(project.value?.imported_members || [])],
    spellcheckEnabled: spellcheckEnabled.value,
    'onUpdate:spellcheckEnabled': (val: boolean) => { spellcheckEnabled.value = val; },
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    uploadFile,
    rewriteFileUrl,
    rewriteReferenceLink,
  }));

  async function performDelete(data: T|null) {
    if (data && project.value && options.performDelete) {
      await options.performDelete(project.value, data);
    }
  }
  async function performSave(data: T|null) {
    if (data && project.value && options.performSave) {
      await options.performSave(project.value, data)
    }
  }
  function updateInStore(data: T|null) {
    if (data && project.value && options.updateInStore) {
      options.updateInStore(project.value, data);
    }
  }

  return {
    data,
    project,
    projectType,
    inputFieldAttrs,
    ...useLockEdit<T|null>({
      data,
      baseUrl,
      hasEditPermissions,
      errorMessage,
      fetchState,
      performSave: options.performSave ? performSave : undefined,
      performDelete: options.performDelete ? performDelete : undefined,
      updateInStore: options.updateInStore ? updateInStore : undefined,
      autoSaveOnUpdateData: options.autoSaveOnUpdateData as (options: { oldValue: T|null, newValue: T|null}) => boolean,
    })
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
