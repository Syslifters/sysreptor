import urlJoin from "url-join";
import { cloneDeep } from "lodash-es";
import { onBeforeRouteLeave, onBeforeRouteUpdate } from "vue-router";
import type { VForm } from "vuetify/lib/components/index.mjs";
import { formatISO9075 } from "date-fns";
import {
  EditMode,
  ProjectTypeScope,
  UploadedFileType,
  type MarkdownEditorMode,
  type PentestProject,
  type ProjectType,
  type UploadedFileInfo,
} from "#imports";
import type { EditToolbar } from "#components";

// @ts-expect-error typeof generic component 
export type ToolbarRef = Ref<InstanceType<typeof EditToolbar>|ComputedRef<InstanceType<typeof EditToolbar>>>;
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
    if (options.fetchState && options.fetchState.status.value !== 'success') {
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
        status: navigationInProgress.value ? 'pending' : options.fetchState ? options.fetchState.status.value : 'success',
      }
    };
  });
  onMounted(() => {
    if (options.updateInStore && data.value) {
      // Set initial value in store to update lock info
      options.updateInStore(cloneDeep(data.value));
    }
  })
  watch(() => options.fetchState?.status.value, async (val) => {
    if (val === 'success' && data.value) {
      if (options.updateInStore) {
        options.updateInStore(cloneDeep(data.value));
      }

      // Scroll to element
      if (route.hash) {
        await nextTick();
        focusElement(route.hash);
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
        deleteConfirmInput: options.deleteConfirmInput?.value || undefined,
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
  hasEditPermissions?: ComputedRef<boolean>;
  errorMessage?: ComputedRef<string|null>;
}) {
  const auth = useAuth();
  const projectType = computed(() => options.projectType.value);

  const baseUrl = computed(() => `/api/v1/projecttypes/${projectType.value.id}/`);
  useHeadExtended({
    title: projectType.value.name
  });

  const hasEditPermissions = computed(() => {
    if (options.hasEditPermissions && !options.hasEditPermissions.value) {
      return false;
    }
    return (projectType.value.scope === ProjectTypeScope.GLOBAL && auth.permissions.value.designer) ||
            (projectType.value.scope === ProjectTypeScope.PRIVATE && auth.permissions.value.private_designs) ||
            (projectType.value.scope === ProjectTypeScope.PROJECT && projectType.value.source === SourceEnum.CUSTOMIZED);
  });
  const errorMessage = computed(() => {
    if (options.errorMessage?.value) {
      return options.errorMessage.value;
    }
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
  const projectType = await useFetchE<ProjectType>(`/api/v1/projecttypes/${projectTypeId}/`, { method: 'GET', deep: true });
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

export function useProjectEditBase(options: {
  project: ComputedRef<PentestProject|undefined|null>,
  projectType?: ComputedRef<ProjectType|undefined|null>,
  historyDate?: string,
  canUploadFiles?: boolean,
  spellcheckEnabled?: Ref<boolean>;
  markdownEditorMode?: Ref<MarkdownEditorMode>;
}) {
  const route = useRoute();
  const auth = useAuth();
  const localSettings = useLocalSettings();
  const projectStore = useProjectStore();

  const projectId = computed(() => options.project.value?.id || route.params.projectId);

  const hasEditPermissions = computed(() => {
    if (options.historyDate) {
      return false;
    } else if (options.project.value && !options.project.value.readonly) {
      return false;
    } else if (!auth.permissions.value.edit_projects) {
      return false;
    }
    return true;
  });
  const errorMessage = computed(() => {
    if (options.historyDate) {
      return `You are comparing a historic version from ${formatISO9075(new Date(options.historyDate))} to the current version.`;
    } else if (options.project.value?.readonly) {
      return 'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.'
    } else if (!auth.permissions.value.edit_projects) {
      return 'You do not have permissions to edit this resource.';
    }
    return null;
  });

  const projectUrl = computed(() => `/api/v1/pentestprojects/${projectId.value}/`);
  const projectTypeUrl = computed(() => options.project.value ? `/api/v1/projecttypes/${options.project.value.project_type}/` : null);

  async function uploadFile(file: File) {
    const uploadUrl = urlJoin(projectUrl.value, options.canUploadFiles ? '/upload/' : '/images/');
    const res = await uploadFileHelper<UploadedFileInfo>(uploadUrl, file);
    if (res.resource_type === UploadedFileType.IMAGE) {
      return `![](/images/name/${res.name}){width="auto"}`;
    } else {
      return `[${res.name}](/files/name/${res.name})`;
    }
  }
  function rewriteFileUrl(fileSrc: string) {
    if (fileSrc.startsWith('/assets/')) {
      return urlJoin(projectTypeUrl.value || '', fileSrc)
    } else {
      return urlJoin(projectUrl.value, fileSrc);
    }
  }

  const referenceItems = computed(() => {
    return projectStore.findings(options.project.value?.id || '', { projectType: options.projectType?.value })
      .map(f => ({
        id: f.id, 
        title: f.data.title,
        riskLevel: options.projectType?.value ? getFindingRiskLevel({ finding: f, projectType: options.projectType?.value }) : undefined,
      }))
  });
  function rewriteReferenceLink(refId: string) {
    const findingRef = referenceItems.value.find(f => f.id === refId);
    if (findingRef) {
      return {
        href: `/projects/${options.project.value!.id}/reporting/findings/${findingRef.id}/`,
        title: `[Finding ${findingRef.title}]`,
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
    lang: options.project.value?.language || 'en-US',
    selectableUsers: [...(options.project.value?.members || []), ...(options.project.value?.imported_members || [])],
    referenceItems: referenceItems.value,
    spellcheckEnabled: spellcheckEnabled.value,
    'onUpdate:spellcheckEnabled': (val: boolean) => { spellcheckEnabled.value = val; },
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    uploadFile,
    rewriteFileUrl,
    rewriteReferenceLink,
  }));

  return {
    hasEditPermissions,
    errorMessage,
    inputFieldAttrs,
  }
}
